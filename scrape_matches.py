import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv
import logging
import unicodedata

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def team_match(team_name, target_team):
    return remove_accents(target_team.lower()) in remove_accents(team_name.lower())

def scrape_match_data(url, target_team):
    logging.info(f"Scraping URL: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    matches = soup.find_all('table', class_='uppercase w-100 fs-12_tp fs-11_ml table_resultats')
    logging.info(f"Found {len(matches)} match tables on the page")
    
    for match in matches:
        teams = match.find_all('a', href=lambda x: x and x.startswith('https://www.fcf.cat/calendari-equip/'))
        if len(teams) == 2:
            home_team = teams[0].text.strip()
            away_team = teams[1].text.strip()
            logging.info(f"Found match: {home_team} vs {away_team}")
            
            if team_match(home_team, target_team) or team_match(away_team, target_team):
                logging.info(f"Match involves {target_team}")
                date_div = match.find('div', class_='tc fs-9 white bg-grey mb-2 lh-data')
                time_div = match.find('div', class_='tc fs-17 white bg-grey')
                
                location_a = match.find('a', href=lambda x: x and x.startswith('https://www.fcf.cat/camp/'))
                location = location_a.text.strip() if location_a else "N/A"
                
                if date_div and time_div:
                    date_str = date_div.text.strip()
                    time_str = time_div.text.strip()
                    logging.info(f"Match details - Date: {date_str}, Time: {time_str}, Location: {location}")
                    return home_team, away_team, date_str, time_str, location
                else:
                    logging.warning("Date or time information missing for the match")
            else:
                logging.info(f"Match does not involve {target_team}")
    
    logging.warning("No matching data found on this page")
    return None, None, None, None, None

base_url = "https://www.fcf.cat/resultats/2425/futbol-11/infantil-primera-divisio-s14/grup-9/jornada-{}"
target_team = "VIAR"  # This will match both "SARRIÀ" and "SARRIA"

# Open a CSV file to write the results
with open('team_matches_calendar.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Write the header for Google Calendar import
    csvwriter.writerow(['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'All Day Event', 'Description', 'Location'])
    
    matches_found = 0
    for jornada in range(1, 31):  # This will check all 30 jornadas
        url = base_url.format(jornada)
        home_team, away_team, date_str, time_str, location = scrape_match_data(url, target_team)
        
        if home_team and away_team and date_str and time_str:
            matches_found += 1
            subject = f"{home_team} vs {away_team}"
            start_date = datetime.strptime(date_str, '%d-%m-%Y').strftime('%m/%d/%Y')
            start_time = time_str
            end_time = (datetime.strptime(time_str, '%H:%M') + timedelta(hours=2)).strftime('%H:%M')  # Assuming 2-hour duration
            description = f"Jornada {jornada}"
            
            csvwriter.writerow([subject, start_date, start_time, start_date, end_time, 'False', description, location])
            logging.info(f"Added match to CSV: {subject} on {start_date}")
        else:
            logging.info(f"No match found for Jornada {jornada}")

    logging.info(f"Total matches found and added to CSV: {matches_found}")

print("CSV file 'team_matches_calendar.csv' has been created with the match data in Google Calendar format.")

