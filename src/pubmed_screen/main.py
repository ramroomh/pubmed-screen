import math
import os
from urllib.parse import quote

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup as bs


def main_menu():
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Welcome to Qwik Search 1.0.")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Qwik Search allows you to optimize your search strategy.")
    while True:
        option = input(
            "Would you like to create a search (enter: 1) or compare searches (enter: 2)?"
        )
        if option == "1":
            break
        elif option == "2":
            break
        else:
            continue
    if option == "1":
        option_1()
    elif option == "2":
        option_2()


def generate_links():
    """This script automates the initial screening phase of systematic search using keywords and does NOT account for duplicates.
    Compatible with the PubMed Database only."""

    # Define keywords
    print("This version of Qwik Search supports two (2) sets of keywords.\n")
    print(
        "Please enter keywords WITHOUT spaces separated by a semicolon (;) (representing 'OR') for each SET of keywords."
    )
    print(
        "For example, entering 'Dopamine;Dopamine Agents' returns the terms: Dopamine OR Dopamine Agents.\n"
    )
    print("Insert an aterisk (*) after a keyword to expand the search of that keyword.")
    print(
        "For example, entering 'Psych*' returns the terms: Psychology, Psychopharmacology.\n"
    )
    print(
        "Use of MeSH terms are encouraged. Please visit https://meshb.nlm.nih.gov/search for more information."
    )
    print("Insert an at sign (@) after a keyword to tag it as a MeSH term.\n")
    while True:
        term1 = input("Please input keywords for the FIRST SET of terms.")
        term1 = list(term1.split(";"))
        term2 = term2 = input("Please input keywords for the SECOND SET of terms.")
        term2 = list(term2.split(";"))
        print(
            "Please enter the filepath separated by '/'. The last entry will be the name of your .csv and .jpg files."
        )
        print("For example: /home/name/Downloads/filename")
        save_path = input("Where would you like to save your results?")
        if term1 and term2 and save_path != None:
            break
    # Results represents the list of lists appropriate for transfer to tabular form
    results = []
    for keyword1 in term1:
        if keyword1.endswith("@"):
            keyword1 = keyword1.replace("@", "")
            fill1 = (quote(keyword1)) + "%5BMeSH+Terms%5D%29"
        else:
            fill1 = quote(keyword1)
        for keyword2 in term2:
            if keyword2.endswith("@"):
                keyword2 = keyword2.replace("@", "")
                fill2 = (quote(keyword2)) + "%5BMeSH+Terms%5D%29"
            else:
                fill2 = quote(keyword2)
            # Create URls by substituting keywords
            URL = (
                "https://pubmed.ncbi.nlm.nih.gov/?term=%28%28"
                + fill1
                + "+AND+%28"
                + fill2
                + "&size=200"
            )
            terms = (keyword1, "AND", keyword2)
            print("Generating URLs for:", terms)
            # Request the URL and parse the content
            page = requests.get(URL)
            view = bs(page.content, "html.parser")
            # Search for the html code representing the # of papers found
            result = view.find("span", {"class": "value"})
            if result != None:
                result = result.get_text(strip=True)
                result = result.replace(",", "")
                result = int(result)
            if result == None:
                result = 0
                result = view.find("span", {"class": "single-result-redirect-message"})
                # Exception for single result searches
                if result != None:
                    result = 1
                if result == None:
                    result = 0
            results.append([URL, terms, result])
    # Transfer list of lists to tabular form
    df = pd.DataFrame(results, columns=["URL", "Terms", "Number of Titles"])
    df.insert(loc=3, column="Cum Sum", value=df["Number of Titles"].cumsum())
    file_name = os.path.join(save_path + "_search_summary.csv")
    df.to_csv(file_name)
    print("URLs generated...")
    return save_path


def get_citations(save_path):
    """Extracts article IDs from URLs."""

    # Get URLs
    file_name = os.path.join(save_path + "_search_summary.csv")
    df = pd.read_csv(file_name, index_col=0)
    notebook = []
    for link in df["URL"]:
        articles = []
        print("Retrieving citations from:", link)
        page = requests.get(link)
        view = bs(page.content, "html.parser")
        result = view.find("span", {"class": "value"})
        if result != None:
            result = result.get_text(strip=True)
            result = result.replace(",", "")
            result = int(result)
            print(result, "citations found.")
            max_pages = math.ceil((result) / 200)
            # Extract PMIDs from PUBMED
            print("Retrieving...", max_pages, "pages.")
            for page in range(1, max_pages + 1):
                new_link = link + "&page=" + str(page)
                page = requests.get(new_link)
                view = bs(page.content, "html.parser")
                print("Downloading:", new_link)
                papers = view.find_all("span", {"class": "citation-part"})
                for paper in papers:
                    paper = paper.get_text(strip=True)
                    if paper.startswith("PMID"):
                        articles.append(paper)
        if result == None:
            print("No citations found.")
        notebook.append(articles)
    # Append data to _citation_IDs.csv
    df_notebook = pd.DataFrame(notebook)
    df_notebook = df_notebook.transpose()
    notebook_name = os.path.join(save_path + "_citation_IDs.csv")
    df_notebook.to_csv(notebook_name)
    return save_path, df, notebook


def count_duplicates(save_path, df, notebook):
    """Counts number of duplicate articles."""

    # Initialize count
    master_counter = {}
    nonduplicates = []
    page = 0
    # loop through _citation_IDs
    for articles in notebook:
        page += 1
        counter = 0
        for i in range(len(articles)):
            check_list = (articles[i]).split()
            for check_it in check_list:
                if check_it not in nonduplicates:
                    counter = counter + 1
                    nonduplicates.append(check_it)
        master_counter.update({page: counter})
    # Append data to the search summary
    df2 = pd.DataFrame.from_dict(master_counter, orient="index")
    df2 = df2.reset_index()
    df2.rename(
        columns={"index": "Search Number", 0: "Number of Non-Duplicates"}, inplace=True
    )
    df2.insert(
        loc=2, column="Cum Non-Dup", value=df2["Number of Non-Duplicates"].cumsum()
    )
    final = pd.concat([df, df2], axis=1)
    final_name = os.path.join(save_path + "_search_summary.csv")
    final.to_csv(final_name)
    return save_path, df, df2


def plot_search(save_path, df, df2):
    """Plots number of duplicate and non-duplicate articles as a function of the # of searches."""

    # Set style
    sns.set_style("dark")
    sns.set_palette("Dark2")
    # Plot data
    alldata = sns.lineplot(x=df2.index, y="Cum Non-Dup", data=df2, linewidth=6)
    alldata = (sns.lineplot(x=df.index, y="Cum Sum", data=df, linewidth=6)).get_figure()
    plt.xlabel("# of Searches")
    plt.ylabel("# of Titles")
    plt.legend(title="Articles", loc="upper left", labels=["Non-Duplicates", "All"])
    # Save data
    alldata.savefig(os.path.join(save_path + ".jpg"), dpi=300)
    print("Data has been saved as", save_path)
    print("Thank you for using Qwik Search. Goodbye!")
    exit()


def percent_overlap():
    """Takes _search_summary.csv files generated from search and calculates % of overlap between search strategies."""

    # User input for file names
    print(
        "Please enter the file path separated by '/' for each search that was generated."
    )
    print("For example: /home/name/Downloads/filename.csv")
    search1_name = input("What is the file path for the first search?")
    search2_name = input("What is the file path for the second search?")
    # Extract data
    search1 = []
    df3 = pd.read_csv(search1_name, index_col=0)
    for d in df3.columns:
        for PMID in df3[str(d)]:
            search1.append(PMID)
    search2 = []
    df4 = pd.read_csv(search2_name, index_col=0)
    for d in df4.columns:
        for PMID in df4[str(d)]:
            search2.append(PMID)
    # Calculate % overlap
    setA = set(search1)
    setB = set(search2)
    overlap = setA & setB
    universe = setA | setB
    result1 = float(len(overlap)) / len(setA) * 100  # % Search 1 in search 2
    result2 = float(len(overlap)) / len(setB) * 100  # % Search 2 in search 1
    result3 = (
        float(len(overlap)) / len(universe) * 100
    )  # overall overlap (middle portion in venn diagram)
    print("% Search 1 in search 2:", result1)
    print("% Search 2 in search 1:", result2)
    print("Overall % overlap:", result3)


def option_1():
    save_path = generate_links()
    save_path, df, notebook = get_citations(save_path)
    save_path, df, df2 = count_duplicates(save_path, df, notebook)
    plot_search(save_path, df, df2)


def option_2():
    percent_overlap()


def main():
    main_menu()


if __name__ == "__main__":
    # execute only if run as a script
    main()
