document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("csv_file");
    const fileName = document.getElementById("file-name");
    const form = fileInput.closest("form");

    fileInput.addEventListener("change", () => {
      if (fileInput.files.length) {
        fileName.textContent = fileInput.files[0].name;
        fileName.classList.remove("error");
      } else {
        fileName.textContent = "ファイルが選択されていません";
        fileName.classList.add("error");
      }
    });

    form.addEventListener("submit", (e) => {
      if (!fileInput.files.length) {
        e.preventDefault();
        fileName.textContent = "ファイルが選択されていません";
        fileName.classList.add("error");
        fileInput.focus();
      }
    });
  });
