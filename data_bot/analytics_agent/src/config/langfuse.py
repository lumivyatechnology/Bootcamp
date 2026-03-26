from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from config import settings

langfuse_instance = Langfuse(
    secret_key=settings.LANGFUSE_SECRET_KEY,
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    environment=settings.LANGFUSE_ENVIRONMENT,
    base_url=settings.LANGFUSE_BASE_URL,
)

langfuse_callback = CallbackHandler()
