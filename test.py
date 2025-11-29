import json
import os
import math
import random
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_users_in_radius(all_users, my_lat, my_lng, radius_km=3.0):
    nearby_users = []
    print(f"[RADAR] Skanowanie w promieniu {radius_km} km od Ciebie...")
    
    for user in all_users:
        if 'lat' not in user: continue

        dist = math.sqrt(
            (user['lat'] - my_lat)**2 + (user['lng'] - my_lng)**2
        ) * 111.0
        
        if dist <= radius_km:
            nearby_users.append(user)
        else:
            pass
            
    return nearby_users

def llm_smart_match(users_list, city_context="Gliwice"):
    if len(users_list) < 2:
        return {"groups": [], "waiting_room": [u['id'] for u in users_list]}

    users_text = json.dumps([
        {"id": u['id'], "name": u['name'], "desc": u['interests']} 
        for u in users_list
    ], ensure_ascii=False)

    system_prompt = f"""
    Jesteś selekcjonerem grup w mieście: {city_context}.
    
    ZASADY KRYTYCZNE (ZŁAMANIE = BŁĄD):
    1. UNIKALNOŚĆ ID: Każde ID użytkownika może wystąpić TYLKO RAZ.
    2. JAKOŚĆ > ILOŚĆ: Nie łącz ludzi na siłę.
    3. POCZEKALNIA: Osoby bez pary wpisz do "waiting_room".
    4. MIEJSCA: Podaj prawdziwe nazwy lokali w {city_context}.

    Zwróć JSON:
    {{
      "groups": [
        {{
          "group_name": "...",
          "venue_name": "...",
          "member_ids": [101, 102],
          "match_quality": "High",
          "reasoning": "..."
        }}
      ],
      "waiting_room": [...]
    }}
    """

    try:
        print(f"[AI] Analizuję {len(users_list)} przefiltrowanych profili...")
        response = client.chat.completions.create(
            model="gpt-5.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": users_text}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2, 
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Błąd AI: {e}")
        return {"groups": [], "waiting_room": []}

if __name__ == "__main__":
    MY_LAT, MY_LNG = 50.294, 18.665

    mock_users = [
        {"id": 101, "name": "Krzysztof", "interests": "python, backend, hackathony, pizza"},
        {"id": 102, "name": "Natalia", "interests": "cosplay, anime, manga, genshin impact"},
        {"id": 103, "name": "Bartek", "interests": "dungeons & dragons, gry planszowe, fantastyka"},
        {"id": 104, "name": "Piotr", "interests": "linux, cyberbezpieczeństwo, ctf, szachy"},
        {"id": 105, "name": "Zuza", "interests": "gry wideo, league of legends, valorant, streamowanie"},
        {"id": 201, "name": "Damian", "interests": "siłownia, crossfit, odżywki białkowe, masa"},
        {"id": 202, "name": "Sebix", "interests": "mma, ksw, boks, bieganie"},
        {"id": 203, "name": "Aneta", "interests": "fitness, zumba, zdrowa żywność, yoga"},
        {"id": 204, "name": "Tomek", "interests": "triathlon, rower szosowy, garmin, bieganie"},
        {"id": 205, "name": "Jarek", "interests": "piłka nożna, orlik, kibicowanie, piwo po meczu"},
        {"id": 301, "name": "Wiktoria", "interests": "kluby, techno, wixapol, instagram"},
        {"id": 302, "name": "Julka", "interests": "prosecco, ploteczki, wyjście na miasto, moda"},
        {"id": 303, "name": "Mati", "interests": "impreza do rana, afterparty, rap, koncerty"},
        {"id": 304, "name": "Klaudia", "interests": "taniec, latino, karaoke, drinki"},
        {"id": 305, "name": "Oskar", "interests": "podrywanie, tinder, kluby studenckie, piwo"},
        {"id": 401, "name": "Basia", "interests": "książki, biblioteka, poezja śpiewana, cisza"},
        {"id": 402, "name": "Filip", "interests": "fotografia analogowa, kawa specialty, wystawy sztuki"},
        {"id": 403, "name": "Monika", "interests": "szydełkowanie, diy, ceramika, herbata"},
        {"id": 404, "name": "Leo", "interests": "gitara, ognisko, muzyka alternatywna, winyle"},
        {"id": 901, "name": "Pan Janusz", "interests": "wędkarstwo, ryby, grzyby, działka"},
        {"id": 902, "name": "Grażyna", "interests": "pieczenie ciast, wnuczki, kościół"},
        {"id": 903, "name": "Foreign Exchange Student", "interests": "english speaking only, sightseeing, monuments"},
    ]

    print("Generowanie pozycji GPS dla użytkowników...")
    for user in mock_users:
        user['lat'] = MY_LAT + (random.uniform(-1, 1) * 0.015) 
        user['lng'] = MY_LNG + (random.uniform(-1, 1) * 0.020)

    for u in mock_users:
        if u['name'] == "Pan Janusz":
            u['lat'] = 50.250
            u['lng'] = 19.000
            print(f"   -> Pan Janusz jest w Katowicach (powinien odpaść z filtra)")

    users_nearby = get_users_in_radius(mock_users, MY_LAT, MY_LNG, radius_km=3.0)
    print(f"Po filtrze lokalizacji zostało: {len(users_nearby)} z {len(mock_users)} osób.")

    result = llm_smart_match(users_nearby, city_context="Gliwice")
    
    if result.get("groups"):
        print(f"\nUTWORZONO GRUPY: {len(result['groups'])}")
        for g in result['groups']:
            names = [u['name'] for u in mock_users if u['id'] in g['member_ids']]
            print(f"   Grupa '{g['group_name']}' @ {g['venue_name']}")
            print(f"   Skład: {names} (Jakość: {g.get('match_quality')})\n")
    
    waiting_ids = result.get("waiting_room", [])
    if waiting_ids:
        print(f"POCZEKALNIA ({len(waiting_ids)} osób):")
        names = [u['name'] for u in mock_users if u['id'] in waiting_ids]
        print(f"   {', '.join(names)}")