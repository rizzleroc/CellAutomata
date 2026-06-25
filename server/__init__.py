"""CellAuto Pro — Railway app server.

A small FastAPI application that:

  * serves the existing free static site (``docs/``) unchanged,
  * gates a high-resolution SEM render endpoint behind Clerk auth + an active
    Stripe subscription,
  * creates Stripe Checkout sessions and consumes Stripe webhooks.

See ``docs/PRD_WEB9_PRO.md`` for the product + operator setup guide. The render
path reuses the tested, tkinter-free ``cellauto.renderer_sem.SemRenderer`` — it
never imports ``cellauto.app`` (which would pull in tkinter), so it runs
headless on a slim container.
"""
