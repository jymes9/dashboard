gcloud builds submit --tag gcr.io/food-sensor-337101/food-sensor  --project=food-sensor-337101

gcloud run deploy --image gcr.io/food-sensor-337101/food-sensor --platform managed  --project=food-sensor-337101 --allow-unauthenticated