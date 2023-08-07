아래의 링크에서 chrome driver를 다운로드해야 동작 가능  
https://chromedriver.chromium.org/downloads
  
1. check_mouse_position.py를 실행하여 확장 버튼을 눌렀을 때, 고정핀을 눌렀을 때, Save page with SingleFile  버튼을 눌렀을 때의 마우스 위치를 기록
2. 기록된 데이터를 바탕으로 자신의 모니터에 맞추어 download_from_naver.py의 코드를 수정. pyautogui가 사용되는 3군데 수정 필요
  
---
전체 페이지 개수 추출  
```javascript
document.querySelectorAll("[class*='EpisodeListView__count--']")  
```
  
현재 페이지의 제목 추출
```javascript
document.querySelectorAll("[class*='EpisodeListList__title--']")  
```
  
페이지 버튼 추출  
```javascript
document.querySelectorAll("button[class*='Paginate__page--']")  
```
  
각 페이지 별 링크 추출  
```javascript
document.querySelectorAll("a[class*='EpisodeListList__link--']")[0].href  
```
  
전체 댓글 더보기  
```javascript
document.querySelectorAll("[class*='u_cbox_btn_view_comment']")[0].click()  
```
  
댓글 더보기  
```javascript
document.querySelectorAll("[class*='u_cbox_more_wrap']")[0].click()  
```

  
아래는 selenium 기준  
```python
driver.find_elements_by_css_selector("button[class*='__page']")
```