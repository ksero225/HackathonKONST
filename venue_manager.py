import time
import os
import json
from dotenv import load_dotenv
from geopy.geocoders import Photon
from openai import OpenAI

load_dotenv()

class VenueManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not found in .env")
        
        self.client = OpenAI(api_key=api_key)
        self.geolocator = Photon(user_agent="hackathon_radar_worker_v2")

    def _get_address_from_coords(self, lat, lng):
        try:
            location = self.geolocator.reverse(f"{lat}, {lng}")
            return location.address if location else "Centrum miasta"
        except Exception as e:
            print(f"Geo error (reverse): {e}")
            return "Twoja Okolica"

    def _get_coords_from_name(self, place_name):
        try:
            location = self.geolocator.geocode(place_name, limit=1)
            if location:
                return {
                    "lat": location.latitude, 
                    "lng": location.longitude, 
                    "address": location.address
                }
            return None
        except Exception as e:
            print(f"Geo error (geocode): {e}")
            return None

    def find_venue(self, lat, lng, category):
        address_context = self._get_address_from_coords(lat, lng)
        print(f"Searching for '{category}' near: {address_context[:40]}...")

        system_prompt = f"""
        Jesteś lokalnym przewodnikiem. 
        Użytkownicy są tutaj: "{address_context}".
        Szukają miejsca kategorii: "{category}".
        
        ZADANIE:
        1. Podaj nazwę JEDNEGO popularnego lokalu/miejsca w tej okolicy (znanego w Google Maps).
        2. Napisz krótki, zachęcający opis tego wydarzenia (max 1 zdanie), ale nie powtarzaj nazwy miejsca.
        
        Zwróć JSON: {{ "place_name": "Nazwa Miejsca, Miasto", "description": "Opis..." }}
        """
        
        default_desc = f"Spotkanie grupy: {category}"

        for attempt in range(3): 
            try:
                response = self.client.chat.completions.create(
                    model="gpt-5.1",
                    messages=[{"role": "system", "content": system_prompt}],
                    response_format={ "type": "json_object" },
                    temperature=0.7
                )
                data = json.loads(response.choices[0].message.content)
                suggested_name = data.get("place_name", "Rynek")
                description = data.get("description", default_desc)
                
                print(f"AI suggests: {suggested_name}")

                real_location = self._get_coords_from_name(suggested_name)
                
                if real_location:
                    print(f"Verified on map: {real_location['lat']}, {real_location['lng']}")
                    return {
                        "name": suggested_name,
                        "address": real_location['address'],
                        "lat": real_location['lat'],
                        "lng": real_location['lng'],
                        "description": description
                    }
                else:
                    print(f"Map failed for '{suggested_name}'. Retrying...")
                    
            except Exception as e:
                print(f"AI Loop Error: {e}")

        print("Using fallback location.")
        return {
            "name": f"Spotkanie w okolicy ({category})",
            "address": address_context,
            "lat": lat,
            "lng": lng,
            "description": default_desc
        }

venue_manager = VenueManager()