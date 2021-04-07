# kabuステーションAPIを利用した自動投資ツール
## 基本情報
* 投資戦略として「[Volatility breakout strategy](https://medium.com/@uprise_crpinv/%E3%83%9C%E3%83%A9%E3%83%86%E3%82%A3%E3%83%AA%E3%83%86%E3%82%A3-%E3%83%96%E3%83%AC%E3%82%A4%E3%82%AF%E3%82%A2%E3%82%A6%E3%83%88-volatility-breakout-vb-%E6%88%A6%E7%95%A5%E3%81%AE%E6%A7%8B%E9%80%A0-2f5e021b84a2)」を使用します。
* 投資対象は手数料が発生しない「[フリーETF](https://kabu.com/item/free_etf/default.html)」になります。
* kabuステーションAPIを利用するために「[auカブコム証券口座](https://kabu.com/)」が必要になります。
* 注文情報/エラー発生情報は「[slack](https://slack.com/intl/ja-jp/)」を通じて携帯に転送されます。
* 各銘柄の時系列データはローカルにあるメータベース(MySQL)に保存されます。

## モジュール / ライブラリ情報
``` python
# 追加要
```
## 基本設定
1. seleniumを使うために自分が利用しているブラウザのバージョンと合うselenium WebDriverをダウンロードします。
  * [Chrome](https://sites.google.com/a/chromium.org/chromedriver/downloads) / [Edge](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) / [Firefox](https://github.com/mozilla/geckodriver/releases) / [Safari](https://webkit.org/blog/6900/webdriver-support-in-safari-10/)
2. WebDriverとをプログラムと同じ場所に配置します。
  * 配置例
  ```
  /.
  ├── main.py
  ├── ...
  └── chromedriver.exe
  ```
3. slackメッセンジャーを利用するための設定
  * [PythonでSlackのBotを作成する方法を現役エンジニアが解説【初心者向け】](https://techacademy.jp/magazine/27979)
4. -- 追加予定 --

## 使用方法
1. DBに時系列データをアップロードします。
  * (フリーETFのリスト入手先追加要)
  * (DBUpdater修正要)
2. main.py, DBUpdater.pyをWindowsのタスクスケジューラに追加します。
  * (手順追加要)
3. 必要によってmain.pyのinitバラメータを修正します。
  * (修正/追加要)

## 実行例

## 注意事項
  * パラメータ調節や個人の株に関する知識によって損失が発生する可能性があり、本開発者には責任がありません。 
