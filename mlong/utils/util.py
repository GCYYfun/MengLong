def get_provider_and_model(model_id):
    provider = model_id.__class__.__name__.lower()
    model = model_id.value
    return provider, model
