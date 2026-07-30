import os
import requests
import pandas as pd
import re

### FUNCTIONS ###

#GET EPPO NAMES AND SYNONYMS

def _get_eppo_names(scientific_name):

    # carica variabili globali
    eppo_token = os.getenv('EPPO_API_KEY')

    headers = {'Accept': 'application/json', 'X-Api-Key': eppo_token}
    
    # 1. Get the EPPO code for the given name
    code_url = "https://api.eppo.int/gd/v2/tools/name2codes"

    try:
        response = requests.get(
            code_url,
            headers=headers,
            params={'name': scientific_name, 'onlyPreferred': 'true'}
            )

        #handle API errors
        response.raise_for_status()

        code_results = response.json()  

        if len(code_results) != 0:   
            eppo_code = code_results[0]['eppocode']
    
            # 2. Get all names/synonyms for that code
            names_url = f"https://api.eppo.int/gd/v2/taxons/taxon/{eppo_code}/names"
            response = requests.get(names_url, headers=headers)
            response.raise_for_status()
            names_data = response.json()
    
            names_df = pd.DataFrame(names_data)

            return names_df['fullname']

        else:
            return f'There is no EPPO code for this name'

    except requests.exceptions.HTTPError:
        return f"Error: bad request — {response.status_code}"

### SCOPUS BIBLIO FAST ANALYSIS ###

def _get_scopus_string_and_count(list_of_names):    

    scopus_token = os.getenv('SCOPUS_API_KEY')

    list_of_names = [name for name in list_of_names if bool(re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s\.\,\-\'\(\)]+", name))]

    # 1. Build the search string
    raw_string = " OR ".join(f'"{name}"' for name in list_of_names)
    scopus_string = f"TITLE-ABS-KEY({raw_string})"

    # 2. Query the API for the paper count only

    url = "https://api.elsevier.com/content/search/scopus"
    headers = {'X-ELS-APIKey': scopus_token, 'Accept': "application/json"}

    try:
        response = requests.get(
            url,
            headers=headers,
            params={'query': scopus_string, 'count': 0}
        )

        response.raise_for_status()
        data = response.json()
        n_scopus_papers = int(data['search-results']['opensearch:totalResults'])
        return f"Scopus query: {scopus_string} | Papers found: {n_scopus_papers}"

    except requests.exceptions.HTTPError:
        return f"Error: Scopus API returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: could not reach Scopus API: {e}"

##WOS BIBLIO FAST ANALYSIS ##

def _get_wos_string_and_count(list_of_names):

    wos_token = os.getenv('WOS_API_KEY')

    #filter out not european languages
    list_of_names = [name for name in list_of_names if bool(re.fullmatch(r"[A-Za-zÀ-ÿ0-9\s\.\,\-\'\(\)]+", name))]

    # 1. Build the search string
    raw_string = " OR ".join(f'"{name}"' for name in list_of_names)
    wos_string = f"TS=({raw_string})"

    # 2. Query the API for the paper count only
    wos_token = os.getenv('WOS_API_KEY', '').strip()
    if not wos_token:
        return "Error: WOS_API_KEY environment variable is not set."

    url = "https://wos-api.clarivate.com/api/wos"
    headers = {'X-ApiKey': wos_token, 'Accept': 'application/json'}
    params = {
        'databaseId': 'WOK',
        'count': 0,  # non serve scaricare i record, solo il totale
        'usrQuery': wos_string,
        'firstRecord': 1
    }

    try:
        response = requests.get(url=url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        wos_count = data['QueryResult']['RecordsFound']
        return f"WoS query: {wos_string} | Papers found: {wos_count}"

    except requests.exceptions.HTTPError:
        return f"Error: WoS API returned {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"Error: could not reach WoS API: {e}"

## @TOOLS ###

def get_eppo_names(scientific_name: str) -> list:
    """
    MANDATORY FIRST STEP for any bibliometric analysis on an organism.
    Retrieves the full list of synonyms and common names for a given
    organism from the EPPO database.

    Always call this tool first, even if you think you already know the
    names — downstream tools (Scopus, Web of Science) require the full
    EPPO-validated list, not just the name the user typed.

    Input: a scientific name, e.g. "Coccus viridis".
    Output: a list of strings with all associated names. Returns an empty
    list if the organism is not found or the request fails.
    """
    names = list(_get_eppo_names(scientific_name))
    return f'The list of EPPO names for {scientific_name} is : {names}'

def get_wos_string_and_count(scientific_name: str) -> str:
    """
    Use the function _get_eppo_names to have a list of EPPO names and
    build a string to query Scopus API.

    Use this when the user wants Web of Science results (search string,
    paper count, or both).

    Input: a list of strings (organism names/synonyms).
    Output: a string containing the WoS query and its paper count, or an
    error message if the request fails.
    """
    list_of_names = list(_get_eppo_names(scientific_name))
    if not list_of_names:
        return f"Error: no EPPO names found for '{scientific_name}'."

    return _get_wos_string_and_count(list_of_names)

def get_scopus_string_and_count(scientific_name: str) -> str:
    """
    Use the function _get_eppo_names to have a list of EPPO names and
    build a string to query Scopus API.

    Use this when the user wants Scopus results (search string, paper count,
    or both).

    a scientific name, e.g. "Coccus viridis".
    Output: a string containing the Scopus query and its paper count, or an
    error message if the request fails.
    """
    list_of_names = list(_get_eppo_names(scientific_name))
    if not list_of_names:
        return f"Error: no EPPO names found for '{scientific_name}'."

    return _get_scopus_string_and_count(list_of_names)


