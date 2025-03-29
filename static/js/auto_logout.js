const checkIntervalSeconds = 60 * 60 * 1; // 1시간마다 검사

function checkAuth() {
  // 토큰 유효성 검사 요청
  fetch("/check-auth", {
    method: "GET",
    credentials: "include"
  })
    .then(response => {
      // 응답이 401오면 자동 로그아웃
      if (response.status === 401) {
        alert("세션이 만료되어 자동 로그아웃되었습니다.");
        window.location.href = "/login";
      }
    })
    .catch(() => {
      alert("네트워크 오류. 다시 로그인해주세요.");
      window.location.href = "/login";
    });
}

window.addEventListener("load", () => {
  // 페이지 로드시 바로 검사
  checkAuth();

  // 1시간마다 반복 검사
  setInterval(checkAuth, checkIntervalSeconds * 1000);
});