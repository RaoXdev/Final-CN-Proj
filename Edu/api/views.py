from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import requests


from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import requests


class NearbySearchView(APIView):
    def get(self, request, *args, **kwargs):
        location = request.query_params.get('location')
        radius = request.query_params.get('radius', 1500)
        place_type = request.query_params.get('type', 'library')
        query = request.query_params.get('q')  # Retrieve query parameter
        start_date = request.query_params.get('start_date')  # YYYY-MM-DD
        end_date = request.query_params.get('end_date')  # YYYY-MM-DD

        if not location:
            return Response({"error": "Location parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        latitude, longitude = location.split(',')

        # --- Google Places API ---
        api_key = settings.GOOGLE_MAPS_API_KEY
        google_places_url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={location}&radius={radius}&type={place_type}&key={api_key}"
        )
        places_response = requests.get(google_places_url)
        places_data = places_response.json() if places_response.status_code == 200 else {}
        if "results" in places_data:
            print("len", len(places_data['results']))
        else:
            print("No results found in places_data")

        # --- PredictHQ API ---
        # phq_api_key = settings.PREDICTHQ_API_KEY
        # phq_url = "https://api.predicthq.com/v1/events/"
        # headers = {"Authorization": f"Bearer {phq_api_key}"}
        # params = {
        #     "location": f"{latitude},{longitude}",
        #     "within": f"{int(radius) // 1000}km",
        #     "category": "conferences,community",
        #     "limit": 20
        # }
        # if query:
        #     params["q"] = query
        # if start_date:
        #     params["start.gte"] = start_date
        # if end_date:
        #     params["start.lte"] = end_date
        #
        # phq_response = requests.get(phq_url, headers=headers, params=params)
        # phq_data = phq_response.json() if phq_response.status_code == 200 else {}
        #
        # # Format for Google Maps
        # formatted_events = []
        # for event in phq_data.get("results", []):
        #     loc = event.get("location", [])
        #     if len(loc) == 2:
        #         formatted_events.append({
        #             "title": event["title"],
        #             "start": event["start"],
        #             "end": event["end"],
        #             "category": event["category"],
        #             "description": event.get("description", ""),
        #             "location": {
        #                 "latitude": loc[1],
        #                 "longitude": loc[0]
        #             }
        #         })

        return Response({
            "places": places_data.get('results', []),
        }, status=status.HTTP_200_OK)


@csrf_exempt
def place_details(request):
    place_id = request.GET.get('placeId')
    if not place_id:
        return JsonResponse({'error': 'placeId parameter is required'}, status=400)

    api_key = settings.GOOGLE_MAPS_API_KEY
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website&key={api_key}'

    try:
        response = requests.get(url)
        return JsonResponse(response.json())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class EducationEventSearchView(APIView):
    def get(self, request):
        location = request.query_params.get("location")
        radius = request.query_params.get("radius", "10")
        # search_term = request.query_params.get("q", "academic")
        start_date = request.query_params.get("start", None)
        # end_date = request.query_params.get("end", None)

        if not location:
            return Response({"error": "Location parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        lat, lon = location.split(',')

        if radius.replace('.', '', 1).isdigit() and not radius.endswith("km"):
            radius = int(radius)//1000
            radius = f"{radius}km"

        headers = {
            "Authorization": f"Bearer {settings.PREDICTHQ_API_KEY}"
        }
        #get place_id
        # id_params = {
        #     "location": f"@{lat},{lon}",
        #     "offset": 10,
        # }
        # place_id = requests.get("https://api.predicthq.com/v1/places/", headers=headers, params=id_params)
        # response_data = place_id.json()
        # results = response_data.get("results", [])
        # print(results)
        # # id =
        # print("id",id)
        # params = {
        #     "place.scope": f"{id}",
        #     "category": "academic,conferences,performing-arts,community",
        #     "sort":"rank",
        # }
        params = {
            "within": f"{radius}@{lat},{lon}",
            "category": "academic,conferences,performing-arts,community",
            "sort": "rank"
        }
        print(radius)
        if start_date:
            params["active.gte"] = start_date
        # if end_date:
        #     params["start.lte"] = end_date

        response = requests.get("https://api.predicthq.com/v1/events/", headers=headers, params=params)
        # print(response.json())
        if response.status_code != 200:
            return Response({"error": "Failed to fetch events", "details": response.json()},
                            status=response.status_code)
        events = [
            {
                "title": e["title"],
                "status": e["state"],
                "start": e["start"],
                "end": e["end"],
                "category": e["category"],
                "location": e.get("location"),
                "description": e.get("description", "")
            }
            for e in response.json().get("results", [])
            if e.get("location")
        ]
        return Response(events, status=200)

class BookSearchView(APIView):
    def get(self, request):

        print(request)
        title = request.query_params.get('title')
        author = request.query_params.get('author')
        # print(request.query_params.get('search-books'))
        if not author and not title:
            return Response({"error": "Please provide author or title of the book."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Generate cache key
        # cache_key = f"book_search:{title}:{author}"
        # cached_data = cache.get(cache_key)
        # if cached_data:
        #     return Response({"books": cached_data})

        base_url = "https://openlibrary.org/search.json"
        params = {}
        if title:
            params['title'] = title
        if author:
            params['author'] = author

        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            return Response({"error": "Failed to fetch data from OpenLibrary"},
                            status=response.status_code)

        data = response.json()
        books = []
        for item in data.get("docs", []):
            books.append({
                "title": item.get("title", "Untitled"),
                "author": ", ".join(item.get("author_name", ["Unknown Author"])),
                "cover_url": f"http://covers.openlibrary.org/b/id/{item['cover_i']}-L.jpg" if item.get(
                    "cover_i") else None,
                "first_publish_year": item.get("first_publish_year", None),
                "key": item.get("key", None)
            })

        # Cache the result for 1 hour
        # cache.set(cache_key, books, timeout=3600)

        return Response({"books": books})
