import argparse
import sys
from pathlib import Path
from urllib.parse import quote

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .esearch import PubMed


def main_menu(api_key):
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("Welcome to PubMed Screen.")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("PubMed Screen allows you to optimize your search strategy.")
    while True:
        option = input(
            "Would you like to create a search (enter: 1) or compare searches (enter: 2)? "
        )
        if option == "1":
            break
        elif option == "2":
            break
        else:
            continue
    if option == "1":
        option_1(api_key)
    elif option == "2":
        option_2()


def screen_keywords(api_key):
    """This script automates the initial screening phase of systematic search using keywords and does NOT account for duplicates.
    Compatible with the PubMed Database only."""

    # Define keywords
    print("This version of PubMed Screen supports two (2) sets of keywords.\n")
    print(
        "Please enter keywords WITHOUT spaces separated by a semicolon (;) (representing 'OR') for each SET of keywords."
    )
    print(
        "For example, entering 'Dopamine;Dopamine Agents' returns the terms: Dopamine OR Dopamine Agents.\n"
    )
    print(
        "Insert an asterisk (*) after a keyword to expand the search of that keyword."
    )
    print(
        "For example, entering 'Psych*' returns the terms: Psychology, Psychopharmacology.\n"
    )
    print(
        "Use of MeSH terms are encouraged. Please visit https://meshb.nlm.nih.gov/search for more information."
    )
    print("Insert an at sign (@) after a keyword to tag it as a MeSH term.\n")
    while True:
        term1 = input("Please input keywords for the FIRST SET of terms: ")
        term1 = list(term1.split(";"))
        term2 = term2 = input("Please input keywords for the SECOND SET of terms: ")
        term2 = list(term2.split(";"))
        print(
            "Please enter the filepath separated by '/'. The last entry will be the name of your .csv and .jpg files."
        )
        print("For example: /home/name/Downloads/filename")
        save_path = input("Where would you like to save your results? ")
        if term1 and term2 and save_path != None:
            break
    # Results represents the list of lists appropriate for transfer to tabular form
    pub_med = PubMed(api_key)
    summary_results = []
    notebook = []
    for keyword1 in term1:
        if keyword1.endswith("@"):
            keyword1 = keyword1.replace("@", "")
            fill1 = keyword1 + "[MeSH Terms]"
        else:
            fill1 = keyword1
        for keyword2 in term2:
            if keyword2.endswith("@"):
                keyword2 = keyword2.replace("@", "")
                fill2 = keyword2 + "[MeSH Terms]"
            else:
                fill2 = keyword2
            # Create query term and URLs by substituting keywords
            query_term = fill1 + " AND " + fill2
            URL = "https://pubmed.ncbi.nlm.nih.gov/?term=" + quote(query_term)
            terms = (keyword1, "AND", keyword2)
            print("Searching for: ", terms)
            # Get search result for terms
            try:
                search_result = pub_med.query(query_term, max_results=9999)
            except Exception as ex:
                print(ex, file=sys.stderr)
                sys.exit(1)
            citation_count = search_result.count
            summary_results.append([URL, terms, citation_count])
            notebook.append(["PMID:" + id for id in search_result.id_list])
            if citation_count > 0:
                print(citation_count, "citations found.")
            else:
                print("No citations found.")

    try:
        # Transfer list of lists to tabular form
        df = pd.DataFrame(summary_results, columns=["URL", "Terms", "Number of Titles"])
        df.insert(loc=3, column="Cum Sum", value=df["Number of Titles"].cumsum())
        file_name = Path(save_path + "_search_summary.csv")
        df.to_csv(file_name)

        # Append data to _citation_IDs.csv
        df_notebook = pd.DataFrame(notebook)
        df_notebook = df_notebook.transpose()
        notebook_name = Path(save_path + "_citation_IDs.csv")
        df_notebook.to_csv(notebook_name)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

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
    final_name = Path(save_path + "_search_summary.csv")
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
    alldata.savefig(Path(save_path + ".jpg"), dpi=300)
    print("Data has been saved as", save_path)
    print("Thank you for using PubMed Screen. Goodbye!")
    exit()


def percent_overlap():
    """Takes _search_summary.csv files generated from search and calculates % of overlap between search strategies."""

    # User input for file names
    print(
        "Please enter the file path separated by '/' for each search that was generated."
    )
    print("For example: /home/name/Downloads/filename.csv")
    search1_name = input("What is the file path for the first search? ")
    search2_name = input("What is the file path for the second search? ")
    # Extract data
    try:
        search1 = []
        df3 = pd.read_csv(Path(search1_name), index_col=0)
        for d in df3.columns:
            for PMID in df3[str(d)]:
                search1.append(PMID)
        search2 = []
        df4 = pd.read_csv(Path(search2_name), index_col=0)
        for d in df4.columns:
            for PMID in df4[str(d)]:
                search2.append(PMID)
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

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


def option_1(api_key):
    save_path, df, notebook = screen_keywords(api_key)
    save_path, df, df2 = count_duplicates(save_path, df, notebook)
    plot_search(save_path, df, df2)


def option_2():
    percent_overlap()


def main():
    parser = argparse.ArgumentParser(
        description="Automates the initial screening phase of systematic PubMed search using keywords"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="print version information and exit",
    )
    parser.add_argument(
        "-k", "--api-key", help="API key for PubMed, increases request rate"
    )
    args = parser.parse_args()

    if args.version:
        from importlib.metadata import version

        print(version("pubmed-screen"))
        sys.exit(0)

    main_menu(args.api_key)


if __name__ == "__main__":
    # execute only if run as a script
    main()
