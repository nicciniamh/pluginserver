document.addEventListener("DOMContentLoaded", function() {
    const isDarkMode = document.documentElement.classList.contains("dark");

    const preElements = document.querySelectorAll("pre");

    preElements.forEach(function(pre) {
        if (isDarkMode) {
            pre.classList.add("github-dark");
            pre.classList.remove("github-light");
        } else {
            pre.classList.add("github-light");
            pre.classList.remove("github-dark");
        }
    });
});

