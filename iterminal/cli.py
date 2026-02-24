"""Simplified CLI entry point using dependency injection."""
import sys
import signal
import logging
from iterminal.config import get_settings
from iterminal.core import get_application_context, shutdown_application_context


# Configure logging
def setup_logging():
    """Setup logging based on settings."""
    settings = get_settings()
    log_level = settings.logging.level.value
    
    logging.basicConfig(
        level=log_level,
        format=settings.logging.format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Add file handler if configured
    if settings.logging.file_path:
        file_handler = logging.FileHandler(settings.logging.file_path)
        file_handler.setLevel(log_level)
        logging.getLogger().addHandler(file_handler)


def handle_interrupt(signum, frame):
    """Handle Ctrl+C gracefully."""
    logging.info("\nShutting down...")
    shutdown_application_context()
    sys.exit(0)


def main():
    """Main entry point."""
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_interrupt)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Get application context (initializes all services)
        context = get_application_context()
        logger.debug("Application context initialized")
        
        # Get settings for info
        settings = context.get_settings()
        logger.info(f"iTerminal started with AI provider: {settings.ai.provider.value}")
        logger.debug(f"Completion enabled: {settings.completion.enabled}")
        
        # Import and call legacy main loop (which now uses new config system)
        from .core_legacy import main_loop
        main_loop()
    
    except KeyboardInterrupt:
        logging.info("\nShutdown requested by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        shutdown_application_context()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main() 