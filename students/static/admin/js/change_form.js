document.addEventListener("DOMContentLoaded", function() {
    window.addEventListener("beforeunload", function() {
      const url = "{{ unlock_url }}";
      if (url) navigator.sendBeacon(url);
    });
  });
