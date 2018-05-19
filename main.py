# -*- coding: utf-8 -*-

import math
import time
import pyautogui as pag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 如果把鼠标光标在屏幕左上角, PyAutoGUI函数就会产生pyautogui.FailSafeException异常
pag.FAILSAFE = False
# 所有pyautogui函数延迟时间
pag.PAUSE = 1

# 解除flash播放限制js代码
unstop_movie = """
    function getPlayer() {
        var _frame1 = window.document.querySelector("iframe");
        var _frame2 = _frame1.contentWindow.document.querySelector("iframe");
        return _frame2.contentWindow.document.querySelector("object");
    }
    function init() {
        var player = getPlayer();
        if (player.getPlayState() !== 1) {
            // if the video has not started, do not enable auto start
            // video metadata should be loaded by player in advance
            setTimeout(init, 1000);
            console.log("Video metadata not loaded. Please click start button.");
            return;
        }
        setInterval(function () {
            try {
                if (player.getPlayState() !== 1)
                    player.playMovie();
            } catch (e) {
            }
        }, 1000);
        console.log("Auto play enabled");
    }
    setTimeout(init, 5000);
"""

# 获取剩余播放时长
get_course_time = """
    var _frame1 = window.document.querySelector("iframe");
    var _frame2 = _frame1.contentWindow.document.querySelector("iframe");
    var player =  _frame2.contentWindow.document.querySelector("object");
    return player.getTotalSecond() - player.getPlaySecond();
"""

# 获取当前播放状态, 返回1代表正在播放
get_player_state = """
    var _frame1 = window.document.querySelector("iframe");
    var _frame2 = _frame1.contentWindow.document.querySelector("iframe");
    var player =  _frame2.contentWindow.document.querySelector("object");
    return player.getPlayState();

"""


class HackErya(object):
    def __init__(self):
        self.username = ""
        self.password = ""
        self.base_url = "http://passport2.chaoxing.com/login?fid="  # 请修改为相应学校的fid值
        # 请在此处修改adblock的id
        self.adblock_url = "chrome-extension://adblock_id/options.html"
        self.slient = {}
        self.play = {}
        self.network = {}
        self.error = {}
        options = Options()
        options.add_argument("disable-infobars")  # 取消自动化控制提示
        options.add_argument('lang=zh_CN.UTF-8')  # 设置中文
        options.add_argument('--ignore-ssl-errors')  # 取消SSL错误提示
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_extension("adblock.crx")
        # 开启flash
        prefs = {
            "RunAllFlashInAllowMode": "true",
            "profile.default_content_settings.state.flash": 1,
            "profile.plugins.flashBlock.enabled": 0,
            "profile.default_content_setting_values.plugins": 1,
            "DefaultPluginsSetting": 1,
            "AllowOutdatedPlugins": 1,
            "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
            "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
            "PluginsAllowedForUrls": "https://mooc1-1.chaoxing.com"
        }
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(executable_path="webDriver/chromedriver", options=options)
        self.action_chains = ActionChains(self.driver)
        self.driver.get(self.adblock_url)  # 在此处打开页面以减少adblock欢迎页面的等待时间
        self.driver.maximize_window()
        self.driver.implicitly_wait(30)  # 隐式等待
        self.wait = WebDriverWait(self.driver, 10)
        # 配置adblock以屏蔽视频中答题的网络请求
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'menubuttons')))
        finally:
            self.driver.find_element_by_class_name("menubuttons").click()  # 自定义
            self.driver.find_element_by_id("btnEditAdvancedFilters").click()  # 编辑
            self.driver.find_element_by_id("txtFiltersAdvanced").send_keys(
                "*.chaoxing.com/richvideo/initdatawithviewer*")  # 屏蔽规则
            self.driver.find_element_by_id("btnSaveAdvancedFilters").click()  # 保存
            self.driver.find_element_by_id("ui-id-2").click()  # 一般设置
            self.driver.find_element_by_id("language_filter_list_1").click()  # 取消勾选easylist, 否则会导致课程视频无法正常播放
            print("配置adblock成功")
        self.close_tab()

    # 用图片匹配得到按钮位置
    def screnshot_button(self):
        # 截图
        size = pag.size()
        pag.click(0, pag.size()[1] / 2, duration=1, tween=pag.easeOutQuad)  # 点击左边界, 确保当前窗口为浏览器界面
        pag.click(size[0] / 2, size[1] / 2, duration=1, tween=pag.easeOutQuad)  # 点击屏幕中央激活flash
        time.sleep(2)  # 确保flash中的静音控件刷新出来
        pag.screenshot("pic/screenshot.png")
        print("截图完成")
        # 定位, 各控件在flash中的相对位置不变，slient, play_button, network, error位置如下
        # (1105.0, 890.0), (360.0, 890), (939.0, 890), (926, 470)
        network_x = 0.88294010
        error_x = 0.99144385
        error_y = 0.53146067
        tmp = pag.locate("pic/slient.png", "pic/screenshot.png", grayscale=True)
        if tmp:
            self.slient["x"] = tmp[0]
            self.slient["y"] = tmp[1]
        else:
            print("无法获取静音控件的位置")
        self.play["x"] = pag.locate("pic/button.png", "pic/screenshot.png", grayscale=True)[0]
        self.play["y"] = self.slient["y"]
        self.network["x"] = int(self.slient["x"] * network_x)
        self.network["y"] = self.slient["y"]
        self.error["x"] = int(self.network["x"] * error_x)
        self.error["y"] = int(self.slient["y"] * error_y)
        sting = 'slient:{slient}, network:{network}, play:{play}, error:{error}'. \
            format(slient=self.slient, network=self.network, play=self.play, error=self.error)
        print(sting)

    def start_movie(self):
        pag.click(self.slient["x"], self.slient["y"], duration=1, tween=pag.easeOutQuad)
        pag.click(self.play["x"], self.play["y"], clicks=2, interval=0.5, duration=1, tween=pag.easeOutQuad)
        pag.moveTo(self.network["x"], self.network["y"], duration=1, tween=pag.easeOutQuad)
        pag.moveRel(0, -35, duration=1, tween=pag.easeOutQuad)
        pag.click()
        pag.click(self.error["x"], self.error["y"], duration=1, tween=pag.easeOutQuad)
        pag.click(self.play["x"], self.play["y"], clicks=2, interval=0.5, duration=1, tween=pag.easeOutQuad)

    def close_tab(self):  # 关闭当前页
        driver = self.driver
        now_handle = driver.current_window_handle
        all_handle = driver.window_handles
        for handle in all_handle:
            if handle != now_handle:
                driver.switch_to.window(handle)
        driver.close()
        driver.switch_to.window(now_handle)
        time.sleep(1)

    # 请手动输入验证码
    def login(self):
        driver = self.driver
        driver.get(self.base_url)
        self.schoolname = driver.find_element_by_xpath("//*[@id=\"schoolName2\"]").text
        username = driver.find_element_by_id("unameId")
        username.send_keys(self.username)
        password = driver.find_element_by_id("passwordId")
        password.send_keys(self.password)
        captcha_content = str(input("captcha: "))
        captcha = driver.find_element_by_id("numcode")
        captcha.send_keys(captcha_content)
        driver.find_element_by_class_name("zl_btn_right").click()
        if "show_error" in driver.page_source:
            print("验证码出错")
            self.login()

    def crack_course(self):
        driver = self.driver
        driver.switch_to.frame("frame_content")
        course_list = driver.find_elements_by_xpath("/html/body/div/div[2]/div[2]/ul/li/div[2]/h3/a")
        courses = [link.text for link in course_list]  # 获取课程列表
        for course in courses:
            print("正在打开课程页：%s" % course)
            driver.find_element_by_link_text(str(course)).click()

        all_handles = driver.window_handles[1:]
        for handle in all_handles:
            driver.switch_to.window(handle)
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "orange")))
                driver.find_element_by_class_name("orange").click()
                next_tag = driver.find_element_by_class_name("orange")
                self.action_chains.move_to_element_with_offset(next_tag, 100, 0).click().perform()
                self.check_finished()
                self.close_tab()
            except Exception as e:
                print(e, "本页面未找到未完成节点")
                self.close_tab()
                continue

    def check_finished(self):
        driver = self.driver
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, 'dct2')))
        except:
            print("视频页面未加载成功")
            self.start_movie()
        finished_tag = pag.locateCenterOnScreen("pic/finished.png")
        if finished_tag is not None:
            print("任务节点已完成, 开始答题")
            self.answer()
        else:
            try:
                driver.switch_to.default_content()  # 切回顶层
                driver.find_element_by_xpath(
                    "//span[@class=\"roundpointStudent  orange01\"]").click()  # 寻找右侧列表中未完成的任务点
                driver.execute_script(unstop_movie)  # 解除暂停播放的限制
                time.sleep(1)
                driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")  # 下拉滚动条
                self.screnshot_button()  # 截图并寻找控件位置
                print("任务节点未完成, 开始播放")
                self.start_movie()  # 开始播放视频
                while driver.execute_script(get_course_time) > 110:  # 还剩120s时网页会自动显示“任务点已完成”, -10s
                    mins = divmod(driver.execute_script(get_course_time), 60)
                    print("剩余时长：%d min %d s" % (int(mins[0]), math.ceil(mins[1])))
                    time.sleep(20)
                    if finished_tag is not None:  # 排除已开始播放但任务点已完成的情况，直接跳到答题
                        print("本章节已完成, 尝试开始答题")
                        self.answer()
                    if driver.execute_script(get_player_state) != 1:
                        print("卡住啦, 尝试重新播放")
                        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")  # 下拉滚动条
                        time.sleep(1)
                        self.start_movie()
            except Exception as e:
                print(e)
            finally:
                print("任务点时间到了, 该答题啦")
                self.check_finished()

    # 无答案直接提交
    def answer(self):
        driver = self.driver
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, 'dct2')))
        except:
            print("答题页面未加载成功")
        try:
            # 跳转至第三层
            driver.switch_to.frame(driver.find_element_by_id("iframe"))
            driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
            driver.switch_to.frame(driver.find_element_by_id("frame_content"))
            print("切换ifram而成功, 开始答题")
            time.sleep(5)
            driver.execute_script("document.getElementsByClassName('Btn_blue_1 marleft10')[0].click()")
            time.sleep(5)
            driver.execute_script("document.getElementsByClassName('bluebtn')[0].click()")
            time.sleep(15)
            self.check_finished()
        except Exception as e:
            print(e, "答题出错")
        self.check_finished()


if __name__ == "__main__":
    driver = HackErya()
    driver.login()
    driver.crack_course()
