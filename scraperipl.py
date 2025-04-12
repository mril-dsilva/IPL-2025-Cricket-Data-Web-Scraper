from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Setup Selenium
options = Options()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service('/Users/mrildsilva/Desktop/chromedriver-mac-arm64/chromedriver')
driver = webdriver.Chrome(service=service, options=options)

# IPL Official Results Page
base_results_url = "https://www.iplt20.com/matches/results"

# Format the Match Date
def format_match_date(date_str):
    try:
        return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error formatting date: {e}")
        return date_str

# Function to get match links
def get_match_links(base_url):
    driver.get(base_url)
    time.sleep(10)
    body = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(20):
        body.send_keys('\ue00f')
        time.sleep(0.5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = []
    match_btns = soup.find_all('a', class_='vn-matchBtn')
    for btn in match_btns:
        href = btn.get('href', '')
        if '/match/' in href:
            if not href.startswith('https://'):
                href = 'https://www.iplt20.com' + href
            if href not in links:
                links.append(href)
    print(f"Total Match Links Found: {len(links)}")
    return links

# Helper: Get powerplay runs
def get_powerplay_runs_sixth_from_bottom():
    try:
        comments = driver.find_elements(By.ID, 'byb__comment')
        if len(comments) >= 6:
            target = comments[-6]
            end_over = target.find_element(By.CLASS_NAME, 'endOverInfo')
            powerplay_text = end_over.find_element(By.CLASS_NAME, 'totRun').text.strip()
            if '/' in powerplay_text:
                return int(powerplay_text.split('/')[0])
            else:
                return int(powerplay_text)
        else:
            print("Warning: Not enough commentary blocks found!")
    except Exception as e:
        print(f"Error in getting sixth-from-bottom powerplay runs: {e}")
    return 'N/A'

# Helper: Get fours and sixes
def get_fours_and_sixes_from_scorecard():
    try:
        sixes_total = 0
        fours_total = 0
        batting_table = driver.find_element(By.CLASS_NAME, 'ap-scroreboard-table')
        headers = batting_table.find_elements(By.TAG_NAME, 'th')
        header_texts = [header.text.strip() for header in headers]
        if '6s' in header_texts and '4s' in header_texts:
            sixes_idx = header_texts.index('6s')
            fours_idx = header_texts.index('4s')
            rows = batting_table.find_elements(By.TAG_NAME, 'tr')[1:]
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, 'td')
                if len(cells) > max(sixes_idx, fours_idx):
                    try:
                        six = int(cells[sixes_idx].text.strip())
                        four = int(cells[fours_idx].text.strip())
                        sixes_total += six
                        fours_total += four
                    except:
                        continue
        else:
            print("Warning: '6s' or '4s' column not found!")
        return fours_total, sixes_total
    except Exception as e:
        print(f"Error scraping fours and sixes: {e}")
        return 0, 0

skipped_matches = []
# Choose scraping order: "latest_first" or "oldest_first"
scrape_order = "oldest_first"  # <-- change to "latest_first" if you want the other way


# Main scraping function
def extract_match_details(match_url):
    driver.get(match_url)
    wait = WebDriverWait(driver, 15)

    time.sleep(7)  # Increased initial load wait

    # Find innings tabs
    try:
        innings_tabs = driver.find_elements(By.CLASS_NAME, 'ap-inner-tb-click')
        time.sleep(7)  # Added wait for innings tabs to stabilize
        if len(innings_tabs) < 2:
            print(f"Warning: Could not find both innings tabs for {match_url}!")
            skipped_matches.append(match_url)
            return None
    except Exception as e:
        print(f"Innings tabs finding error: {e}")
        skipped_matches.append(match_url)
        return None

    # TEAM names
    team1 = innings_tabs[0].text.strip().split()[0] if len(innings_tabs) > 0 else 'N/A'
    team2 = innings_tabs[1].text.strip().split()[0] if len(innings_tabs) > 1 else 'N/A'

    ## Scrape Venue and Date
    try:
        venue_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="bannerDiv"]/section/div/h3/span[1]')))
        date_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="bannerDiv"]/section/div/h3/span[2]')))
        venue = venue_element.text.strip()
        match_date = date_element.text.strip()
        match_date = format_match_date(match_date)

    except Exception as e:
        print(f"Error scraping venue/date: {e}")
        venue = 'N/A'
        match_date = 'N/A'

    ## TEAM 1: first batting team powerplay
    try:
        innings_tabs[0].click()
        time.sleep(7)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        wait.until(EC.presence_of_element_located((By.ID, 'byb__comment')))
        time.sleep(2)
        team1_runs_6 = get_powerplay_runs_sixth_from_bottom()
    except Exception as e:
        print(f"Click/scroll Team 1 error: {e}")
        team1_runs_6 = 'N/A'

    ## TEAM 2: second batting team powerplay
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        innings_tabs = driver.find_elements(By.CLASS_NAME, 'ap-inner-tb-click')
        time.sleep(3)
        innings_tabs[1].click()
        time.sleep(7)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        wait.until(EC.presence_of_element_located((By.ID, 'byb__comment')))
        time.sleep(2)
        team2_runs_6 = get_powerplay_runs_sixth_from_bottom()
    except Exception as e:
        print(f"Click/scroll Team 2 error: {e}")
        team2_runs_6 = 'N/A'

    ## WINNER
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    winner_div = soup.find('div', class_='ms-matchComments')
    winner = winner_div.text.strip() if winner_div else 'N/A'

    ## SIXES and FOURS
    sixes = [0, 0]
    fours = [0, 0]
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        scorecard_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-id='scoreCard']"))
        )
        driver.execute_script("arguments[0].click();", scorecard_tab)
        print("Clicked Scorecard tab successfully ✅")
        time.sleep(5)

        innings_tabs = driver.find_elements(By.CLASS_NAME, 'ap-inner-tb-click')
        time.sleep(3)

        # --- Team 1 Fours and Sixes ---
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            driver.execute_script("arguments[0].click();", innings_tabs[0])
            time.sleep(7)
            fours[0], sixes[0] = get_fours_and_sixes_from_scorecard()
        except Exception as e:
            print(f"Team 1 Fours/Sixes error: {e}")

        # --- Team 2 Fours and Sixes ---
        try:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            innings_tabs = driver.find_elements(By.CLASS_NAME, 'ap-inner-tb-click')
            time.sleep(3)
            driver.execute_script("arguments[0].click();", innings_tabs[1])
            time.sleep(7)
            fours[1], sixes[1] = get_fours_and_sixes_from_scorecard()
        except Exception as e:
            print(f"Team 2 Fours/Sixes error: {e}")

    except Exception as e:
        print(f"Scorecard section scraping error: {e}")

    # Validate if match was scraped properly
    if team1_runs_6 == 'N/A' and team2_runs_6 == 'N/A' and sixes == [0, 0]:
        print(f"Skipping incomplete match: {team1} vs {team2}")
        skipped_matches.append(match_url)
        return None

    # --- DEBUG PRINT ---
    print(f"\nScraping Match: {team1} vs {team2}")
    print(f"Venue: {venue}")
    print(f"Date: {match_date}")
    print(f"Winner: {winner}")
    print(f"Team 1 Powerplay (6 Overs): {team1_runs_6}")
    print(f"Team 2 Powerplay (6 Overs): {team2_runs_6}")
    print(f"Team 1 Fours: {fours[0]}")
    print(f"Team 2 Fours: {fours[1]}")
    print(f"Team 1 Sixes: {sixes[0]}")
    print(f"Team 2 Sixes: {sixes[1]}")

    return {
        'Match': f'{team1} vs {team2}',
        'Venue': venue,
        'Date': match_date,
        'Winner': winner,
        'Team 1 Powerplay Runs': team1_runs_6,
        'Team 2 Powerplay Runs': team2_runs_6,
        'Team 1 Fours': fours[0],
        'Team 2 Fours': fours[1],
        'Team 1 Sixes': sixes[0],
        'Team 2 Sixes': sixes[1]
    }

# Main script
match_links = get_match_links(base_results_url)
data = []
print(f"Found {len(match_links)} match links. Scraping details...\n")

# Decide match link order
match_links_to_scrape = match_links if scrape_order == "latest_first" else list(reversed(match_links))

try:
    for idx, link in enumerate(match_links_to_scrape):
        details = extract_match_details(link)
        if details:
            data.append(details)
            df_temp = pd.DataFrame(data)
            df_temp.to_csv('ipl_2025_partial.csv', index=False)
        print(f"Scraped {idx+1} match(es)...")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nScraping interrupted manually! Saving partial data...")
finally:
    if data:
        df = pd.DataFrame(data)
        df.to_csv('ipl_2025_final.csv', index=False)
        print("Saved final data to ipl_2025_final.csv")
        
    else:
        print("No match data found.")
    driver.quit()