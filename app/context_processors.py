from flask import current_app

from app.auth import login_manager


def _register_context_processors(app):
    @app.context_processor
    def inject_globals():
        from flask_login import current_user

        return {
            "FORMAS_PAGAMENTO": current_app.config["FORMAS_PAGAMENTO"],
            "MAX_PARCELAS": current_app.config["MAX_PARCELAS"],
            "current_user": current_user,
        }
