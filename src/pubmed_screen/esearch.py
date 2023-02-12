import time

import requests

class SearchResult:
    """A SearchResult object holds all of the information returned by
    a PubMed search query."""
    def __init__(self, query_response):
        self.request_url = query_response.url
        self.search_result = query_response.json()["esearchresult"]

    @property
    def url(self):
        """URL for the search request"""
        return self.request_url

    @property
    def count(self):
        """Number of PMID results"""
        return self.search_result["count"]
    
    @property
    def id_list(self):
        """A list of PMIDs"""
        return self.search_result["idlist"]

    @property
    def query_translation(self):
        """A canonical representation of the search term"""
        return self.search_result["querytranslation"]

    def __repr__(self):
        return str(self.search_result)


class PubMed:
    def __init__(self, api_key=None):
        self.api_key = api_key
        if self.api_key:
            # 10 requests per second with an API key
            self.min_interval = 0.100
        else:
            # 3 requests per second without an API key
            self.min_interval = 0.333
        self.last_query = 0.0
        self.last_url = None
        self.last_search_result = None

    def query(self, term, max_results=200):
        """Returns a SearchResult object for the given search term"""
        if max_results > 10000:
            raise ValueError("max_results cannot be larger than 10000")

        # Enforce minimum intervals between calls
        interval = time.time() - self.last_query
        if interval < self.min_interval:
            time.sleep(self.min_interval - interval)
        self.last_query = time.time()

        # Send search request
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": term,
            "retmax": max_results,
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        response = requests.get(url, params)
        response.raise_for_status()
        self.last_url = response.url
        self.last_search_result = response.json()["esearchresult"]
        return SearchResult(response)


if __name__ == "__main__":
    pub_med = PubMed()
    result = pub_med.query("asthma[mh] AND (dopamine[mh] OR dopamine agents[mh])")
    print(result.url)
    print(result.count)
    print(result.id_list)
    print(result.query_translation)
