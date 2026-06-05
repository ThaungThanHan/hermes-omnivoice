"""Directory-plugin entry point for Hermes Agent.

This file lets the repository be copied directly into
``~/.hermes/plugins/omnivoice``. The package entry point used by pip installs
also delegates to the same register function.
"""

from .hermes_omnivoice import register

__all__ = ["register"]
