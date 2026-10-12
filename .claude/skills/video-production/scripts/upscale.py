#!/usr/bin/env python3
"""4x upscale with Real-ESRGAN realesr-general-x4v3 (SRVGGNetCompact) without torch:
parse the .pth zip with a minimal unpickler, rebuild the network as an ONNX graph, run it tiled with onnxruntime.
   python3 upscale.py in.png out.png"""
import collections, os, pickle, sys, time, zipfile
import numpy as np
import onnx
from onnx import helper, TensorProto, numpy_helper
import onnxruntime as ort
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PTH = os.environ.get("REALESRGAN_PTH", os.path.join(HERE, "models", "realesr-general-x4v3.pth"))  # fetch: references/stills-to-motion.md


def load_pth(path):
    zf = zipfile.ZipFile(path)
    prefix = zf.namelist()[0].split("/")[0]
    dt = {"FloatStorage": np.float32, "HalfStorage": np.float16, "DoubleStorage": np.float64, "LongStorage": np.int64}

    def rebuild(storage, offset, size, stride, *args):
        if len(size) == 0:
            return storage[offset].copy()
        return np.lib.stride_tricks.as_strided(storage[offset:], shape=tuple(size), strides=tuple(s * storage.itemsize for s in stride)).copy()

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if mod == "torch._utils" and name == "_rebuild_tensor_v2":
                return rebuild
            if mod == "torch" and name.endswith("Storage"):
                return name
            if mod == "collections" and name == "OrderedDict":
                return collections.OrderedDict
            return super().find_class(mod, name)

        def persistent_load(self, pid):
            _, stype, key, loc, numel = pid
            stype = stype if isinstance(stype, str) else getattr(stype, "__name__", str(stype))
            return np.frombuffer(zf.read(f"{prefix}/data/{key}"), dtype=dt[stype])

    return U(zf.open(f"{prefix}/data.pkl")).load()


def build_onnx(sd, scale=4):
    keys = sorted({int(k.split(".")[1]) for k in sd if k.startswith("body.")})
    nodes, inits = [], []
    cur = "x"
    for i in keys:
        w = sd[f"body.{i}.weight"]
        if w.ndim == 4:
            inits += [numpy_helper.from_array(w.astype(np.float32), f"w{i}"), numpy_helper.from_array(sd[f"body.{i}.bias"].astype(np.float32), f"b{i}")]
            nodes.append(helper.make_node("Conv", [cur, f"w{i}", f"b{i}"], [f"c{i}"], kernel_shape=[3, 3], pads=[1, 1, 1, 1]))
            cur = f"c{i}"
        else:
            inits.append(numpy_helper.from_array(w.reshape(-1, 1, 1).astype(np.float32), f"a{i}"))
            nodes.append(helper.make_node("PRelu", [cur, f"a{i}"], [f"p{i}"]))
            cur = f"p{i}"
    nodes.append(helper.make_node("DepthToSpace", [cur], ["ps"], blocksize=scale, mode="CRD"))
    inits.append(numpy_helper.from_array(np.array([1, 1, scale, scale], np.float32), "scales"))
    nodes.append(helper.make_node("Resize", ["x", "", "scales"], ["base"], mode="nearest"))
    nodes.append(helper.make_node("Add", ["ps", "base"], ["y"]))
    g = helper.make_graph(nodes, "srvgg", [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, None, None])],
                          [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 3, None, None])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)])
    m.ir_version = 8
    onnx.checker.check_model(m)
    return m


def main(src, dst, tile=256, pad=12):
    ck = load_pth(PTH)
    sd = ck.get("params", ck.get("params_ema", ck))
    sess = ort.InferenceSession(build_onnx(sd).SerializeToString(), providers=["CPUExecutionProvider"])
    img = np.asarray(Image.open(src).convert("RGB"), np.float32) / 255.0
    Hh, Ww, _ = img.shape
    out = np.zeros((Hh * 4, Ww * 4, 3), np.float32)
    t0 = time.time()
    for y0 in range(0, Hh, tile):
        for x0 in range(0, Ww, tile):
            ya, yb = max(0, y0 - pad), min(Hh, y0 + tile + pad)
            xa, xb = max(0, x0 - pad), min(Ww, x0 + tile + pad)
            x = img[ya:yb, xa:xb].transpose(2, 0, 1)[None]
            y = sess.run(None, {"x": np.ascontiguousarray(x)})[0][0].transpose(1, 2, 0)
            oy, ox = (y0 - ya) * 4, (x0 - xa) * 4
            th, tw = min(tile, Hh - y0) * 4, min(tile, Ww - x0) * 4
            out[y0 * 4:y0 * 4 + th, x0 * 4:x0 * 4 + tw] = y[oy:oy + th, ox:ox + tw]
        print(f"  row {y0}/{Hh}  {time.time() - t0:.0f}s", flush=True)
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)
    print("saved", dst, out.shape)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
