from core.celery_app import app


@app.task(bind=True)
def process_payout(self, payout_id):
    # chlo bhai shuru hojao
    
    pass