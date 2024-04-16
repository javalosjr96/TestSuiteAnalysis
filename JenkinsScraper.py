import csv
import re
import os
import datetime
import sys
import requests

from bs4 import BeautifulSoup

def remove_all_commas(console_log):
    pattern = r","
    if console_log:
        return re.sub(pattern, "", console_log)


def get_html_content(url, filename):
    try:
        response = requests.get(url)
        response.raise_for_status()

        with open(filename, "wb") as f:
            f.write(response.content)

        with open(filename, "r") as f:
            html_content = f.read()
            return html_content

    except requests.exceptions.RequestException as e:
        print(f"Error downloading HTML: {e}")
        exit(1)


def get_error_and_context(lines):
    error_stacktraces = []
    error_found = False
    context_lines = []
    error_regex = r"\s+ERROR\s+\[.+\]"

    for line in lines:
        if re.search(error_regex, line) and not error_found:
            error_found = True

        if error_found:
            context_lines.append(line)
            if len(context_lines) == 50:
                string_data = ''.join(context_lines)
                error_stacktraces.append(string_data)
                context_lines = []
                error_found = False

    if error_stacktraces:
        return error_stacktraces
    else:
        return None


def scrape_jenkins_html(url):
    jenkins_html_content = get_html_content(url, "jenkins.html")

    soup = BeautifulSoup(jenkins_html_content, "html.parser")

    anchor_tags = soup.find_all('a', string=lambda text: text and "PR#" in text)

    if anchor_tags:
        pr_link = anchor_tags[0]['href']
        pr_row.append(pr_link)

    else:
        print("No link found containing 'PR#'")

    tables = soup.find_all('table')

    for table in tables:
        if table.caption and (table.caption.text.startswith("---- Unstable: ") or table.caption.text.startswith(
                "---- Failure: ") or table.caption.text.startswith("---- Aborted: ")):
            for row in table.find_all('tr'):
                if any(cell.text.strip() == 'Console' for cell in row.find_all('td')):
                    row_data = []
                    for cell in row.find_all('td'):
                        cell_text = cell.text.strip()
                        if '+' in cell_text:
                            continue
                        cell_text = cell_text.replace(",", "")
                        if cell.find('a') and cell.find('a').text == 'Console':
                            console_url = cell.find('a')['href']
                            console_url = f"{console_url}Text"
                            console_log_urls.append(console_url)
                            cell_text = f"{console_url}"
                        if cell.find('a') and cell.find('a').text == 'Test Report':
                            report_url = cell.find('a')['href']
                            cell_text = f"{report_url}"
                            test_report_urls.append(report_url)
                        row_data.append(cell_text)
                    string_data = ','.join(row_data)
                    scraped_jenkins_html.append(string_data)


def scrape_test_report(test_report_url):
    test_report_content = get_html_content(test_report_url, "test_report.html")
    soup = BeautifulSoup(test_report_content, 'html.parser')
    all_links = soup.find_all('a')

    desired_links = [link for link in all_links if
                     link.get('id') and link['id'].startswith("test-") and link['id'].endswith("-showlink")]
    if desired_links:
        extracted_text = desired_links[0]['id'].split("test-")[1].split("-showlink")[0]
        stacktrace_url = test_report_url + "/" + extracted_text
        stacktrace_content = get_html_content(stacktrace_url, "stack_trace.html")
        pattern = r"<h3>Stacktrace</h3><pre>(.*?)</pre>"

        match = re.search(pattern, stacktrace_content, re.DOTALL)

        if match:
            error_data = match.group(1)
            return error_data


def scrape_test_case_names(test_report_url):
    test_report_content = get_html_content(test_report_url, "test_report.html")
    soup = BeautifulSoup(test_report_content, 'html.parser')
    all_links = soup.find_all('a')

    desired_links = [link for link in all_links if
                     link.get('id') and link['id'].startswith("test-") and link['id'].endswith("-showlink")]

    if desired_links:
        extracted_text = desired_links[0]['id'].split("test-")[1].split("-showlink")[0]
        test_case_names.append(extracted_text)


def cleanUp():
    files = ["jenkins.html", "stack_trace.html", "test_report.html", "console_logs.txt"]
    for file in files:
        try:
            os.remove(file)
        except FileNotFoundError:
            print("Error: File not found.")
    print("Clean Up Successful")


def scrape_logs():
    today = datetime.date.today().strftime("%m-%d.csv")  # Get formatted date (month-day)
    console_log_urls_counter = 0
    scraped_jenkins_html_counter = 0
    for console_log_url in console_log_urls:
        response = requests.get(console_log_url)
        if response.status_code == 200:
            with open("console_logs.txt", 'wb') as file:
                file.write(response.content)
        else:
            print(f"Error downloading logs: {response.status_code}")

        with open("console_logs.txt", "r") as f:
            error_stacktraces = get_error_and_context(f.readlines())
            if error_stacktraces:
                error_stack = ''.join(error_stacktraces)
                error_stack = remove_all_commas(error_stack)
                global_error_stacktraces.append(error_stack)
            else:
                report_stack = scrape_test_report(test_report_urls[console_log_urls_counter])
                if report_stack:
                    report_stack = remove_all_commas(report_stack)
                else:
                    report_stack = "No error found | Check for Timeout"
                global_error_stacktraces.append(report_stack)

        console_log_urls_counter += 1

    for stacktrace in global_error_stacktraces:
        test_case_row = scraped_jenkins_html[scraped_jenkins_html_counter] + ","
        scraped_jenkins_html_counter += 1
        test_case_row = test_case_row + stacktrace
        test_case_csv.append(test_case_row)

    for test_report_url in test_report_urls:
        scrape_test_case_names(test_report_url)

    test_case_names_list = list(set(test_case_names))

    with open(today, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(pr_row)
        writer.writerow(header_row)
        for entry in test_case_csv:
            data_list = entry.split(",")
            writer.writerow(data_list)
        writer.writerow("")
        writer.writerow(footer_row)
        for test_name in test_case_names_list:
            writer.writerow(["", "", "", "", "", "", test_name])


header_row = ["Console", "Test Report", "Date", "Build Time", "Status", "Result", "Stacktraces"]

footer_row = ["Jira Tickets", "Stacktrace", "Component", "Product Team", "Priority", "", "Test Cases"]

scraped_jenkins_html = []
global_error_stacktraces = []
console_log_urls = []
test_report_urls = []
test_case_csv = []
test_case_names = []
pr_row = ["Pull Request:"]

if len(sys.argv) > 1:
    jenkinsUrl = sys.argv[1]
    print(f"Jenkins URL: {jenkinsUrl}")
else:
    print("No argument provided.")

scrape_jenkins_html(jenkinsUrl)

scrape_logs()

cleanUp()
