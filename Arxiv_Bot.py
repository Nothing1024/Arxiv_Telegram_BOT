import requests
import notify
from bs4 import BeautifulSoup
ARXIV_BASE = "https://arxiv.org/"
NEW_SUB_URL = 'https://arxiv.org/list/cs/new'
I18N_LIBRARY = { 
    "Chinese":{"Title":"Arxiv每日播报：", "Keyword":"关键词：", "Authors":"作者：", "Subjects":"主题：", "Arxiv link":"Arxiv地址：", "PDF link":"PDF地址：", "Abstract":"文章摘要：","NoneOutput":"暂未找到结果"},
    "English":{"Title":"Daily Arxiv:","Keyword":"Keyword:", "Authors":"Authors:", "Subjects":"Subjects:", "Arxiv link":"Arxiv link:", "PDF link":"PDF link:", "Abstract":"Abstract:", "NoneOutput":"There is no result" }
}

# 自定义配置
KEYWORD_LIST = ["Action Recognition", "transformer"] # 查询关键字，大小写均可
I18N_DICT = I18N_LIBRARY["Chinese"] #多语言选择 中文或英文


def TG_BOT_Push(today_title,keyword_list,keyword_dict):
    def TG_BOT_formatter(today_title,keyword_list,keyword_dict):
        full_report = []

        def checkWordLimit(report, update):
            if(len(report + update) > 4096):
                full_report.append(report)
                report = ""
            return report + update
        report = "*" + I18N_DICT['Title'] + today_title.replace("New submissions for ","") +"*" + "\n\n"

        for keyword in keyword_list:
            report = checkWordLimit(report, '*'+I18N_DICT['Keyword']+' ' + keyword + "*"'\n\n')
            if len(keyword_dict[keyword]) == 0:
                report = checkWordLimit(report, I18N_DICT['NoneOutput'] + '\n')
            for paper in keyword_dict[keyword]:
                temp_report = str('*{}*\n - *'+I18N_DICT['Authors']+'* {}\n - *'+I18N_DICT['Subjects']+'* {}\n - *'+I18N_DICT['Arxiv link']+'* {}\n - *'+I18N_DICT['PDF link']+'* {}\n - *'+I18N_DICT['Abstract']+'* {}') \
                    .format(paper['title'], paper['authors'], paper['subjects'], paper['main_page'], paper['pdf'],
                            paper['abstract'])
                report = checkWordLimit(report, temp_report + '\n')
            report = checkWordLimit(report,"---------------\n")
        full_report.append(report)
        return full_report

    try:
        for i in TG_BOT_formatter(today_title,keyword_list,keyword_dict):
            notify.send(title=I18N_DICT["Title"], content=i)
    except Exception as e:
        print("推送失败",e.__str__())
        notify.send(title='Arxiv每日播报推送失败', content=str(e.__str__()))

def getArxivMeta():
    header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.105 Safari/537.36'}
    response_data = "空"
    try:
        r = requests.get(NEW_SUB_URL, headers=header)
        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.body.find("div", {'id': 'content'})
        # 获取今日arxiv标题
        today_title = content.find("h3").text
        # 获取dt标题(arXiv:2203.13277 [pdf, other])和dd标题(内容)
        dt_list = content.dl.find_all("dt")
        dd_list = content.dl.find_all("dd")
        assert len(dt_list) == len(dd_list) # 如果dt和dd对不上，则意味着有额外元素，直接退出
        keyword_list = KEYWORD_LIST
        keyword_dict = {key: [] for key in keyword_list}
        for i in range(len(dt_list)):
            paper = {}
            # 获取论文编号 例：[1]   arXiv:2203.13258 [pdf]->arXiv:2203.13258->2203.13258
            paper_number = dt_list[i].text.strip().split(" ")[2].split(":")[-1]
            # 拼接正文链接 例：https://arxiv.org/abs/2203.13258
            paper['main_page'] = ARXIV_BASE + "abs/" + paper_number
            # 拼接pdf下载地址 例：https://arxiv.org/abs/2203.13258
            paper['pdf'] = ARXIV_BASE + "pdf/" + paper_number
            # 修改论文标题，可能是为了防止Title内容重复
            paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title: ", "").strip()
            # 修改论文作者，可能是为了防止Authors内容重复
            paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text.replace("Authors:\n", "").replace("\n", "").strip()
            # 修改主题，可能是为了防止Subjects内容重复
            paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
            # 修改主题,清除"\n"
            paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()

            # 检测关键字是否存在
            for keyword in keyword_list:
                if keyword.lower() in paper['abstract'].lower():
                    keyword_dict[keyword].append(paper)
    except Exception as e:
        print("爬取失败",e.__str__())
    return today_title,keyword_list,keyword_dict        

def main():
    TG_BOT_Push(*getArxivMeta())
        
if __name__ == '__main__':
    main()
