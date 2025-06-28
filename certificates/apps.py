from django.apps import AppConfig


class CertificatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certificates'
    verbose_name = 'Certificates Management'
    
    def ready(self):
        # Import signals last to avoid AppRegistryNotReady issues
        try:
            import certificates.signals  # noqa
        except ImportError:
            # Skip if signals can't be imported
            pass
