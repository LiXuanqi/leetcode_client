import requests
from bs4 import BeautifulSoup

LEETCODE_URLS = {
        'base': 'https://leetcode.com',
        'login': 'https://leetcode.com/accounts/login/',
        'graphql': 'https://leetcode.com/graphql',
} 
levelToDifficulty = {
    1: 'Easy',
    2: 'Medium',
    3: 'Hard',
}
class LeetCodeClient:

    def __init__(self):
        self.session = requests.Session() 
        self.categories = ['algorithms']

    def isLogin(self):
        return 'LEETCODE_SESSION' in self.session.cookies
       
    def login(self, username, password):
        res = self.session.get(LEETCODE_URLS['login']) 

        if res.status_code != 200:
            return False
        
        headers = {
                'Origin': 'https://leetcode.com',
                'Referer': LEETCODE_URLS['login'],
        }

        data = {
                'csrfmiddlewaretoken': self.session.cookies['csrftoken'],
                'login': username,
                'password': password,
        }
        res = self.session.post(
            LEETCODE_URLS['login'],
            data=data,
            headers=headers,
            allow_redirects=False,  # if login success, the page will redirect.
        )
        if res.status_code != 302:
            # wrong password.
            return False
        return True

    def _make_headers(self):
        return {
            'Origin': LEETCODE_URLS['base'],
            'Referer': LEETCODE_URLS['base'],
            'X-CSRFToken': self.session.cookies['csrftoken'],
            'X-Requested-With': 'XMLHttpRequest',
        }

    def getProblemsByCategory(self, category):
        problems = []
        if category not in self.categories:
            return []
        # request
        headers = self._make_headers()
        res = self.session.get(f'https://leetcode.com/api/problems/{category}', headers=headers).json()
        for row in res['stat_status_pairs']:
            problem = Problem(row)
            problems.append(problem)

        return problems
    
    def getProblems(self):
        problems = []
        for category in self.categories:
            subProblems = self.getProblemsByCategory(category)
            problems.extend(subProblems)

        return sorted(problems, key=lambda problem: problem.id)
        

    def getProblemBySlug(self, slug):
        headers = self._make_headers()
        headers['Referer'] = f'https://leetcode.com/problems/{slug}/description'
        body = {'query': '''query getQuestionDetail($titleSlug : String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    content
    stats
    difficulty
    codeDefinition
    sampleTestCase
    enableRunCode
    translatedContent
  }
}''',
            'variables': {'titleSlug': slug},
            'operationName': 'getQuestionDetail'}
        res = self.session.post(LEETCODE_URLS['graphql'], json=body, headers=headers)
        if res.status_code != 200:
            return
        res = res.json()['data']['question']
        print(res)
        soup = BeautifulSoup(res['translatedContent'] or res['content'], features='html.parser')
# TODO: create decorator to check login status

class Problem:

    def __repr__(self):
        return f'{self.id} | {self.title} | {self.difficulty} | {self.slug}\n'
    def __init__(self, rawData):
        stat = rawData['stat']
        self.id = stat['question_id']
        self.slug = stat['question__title_slug']
        self.title = stat['question__title']
        self.hidden = stat['question__hide']
        self.total_acs = stat['total_acs']
        self.total_submitted = stat['total_submitted']
        self.frontend_question_id = stat['frontend_question_id']
        self.is_new = stat['is_new_question']
        self.status = rawData['status']
        self.difficulty = levelToDifficulty[rawData['difficulty']['level']]
        self.paid_only = rawData['paid_only']
        self.is_favor = rawData['is_favor']
        self.frequency = rawData['frequency']

if __name__ == "__main__":
    client = LeetCodeClient()
    res = client.login()
    print(client.getProblems())
    client.getProblemBySlug('find-in-mountain-array')
