  function toggleSidebar() {
    var bar = document.getElementById("mySidebar");
    if (bar.classList.contains("w3-hide")) {
      bar.classList.remove("w3-hide");
      document.getElementById("main").style.paddingLeft = "250px";
      document.getElementById("header").style.paddingLeft = "250px";
      document.getElementById("footer").style.marginLeft = "250px";
    } else {
      bar.classList.add("w3-hide");
      document.getElementById("main").style.paddingLeft = "0";
      document.getElementById("header").style.paddingLeft = "0";
      document.getElementById("footer").style.marginLeft = "0";
    }
  }
  
  function toggleAppsMenu() {
    var panel = document.getElementById("AppsPanel");
    if (panel.classList.contains("w3-hide")) {
      panel.classList.remove("w3-hide");
    } else {
      panel.classList.add("w3-hide");
    }
  }