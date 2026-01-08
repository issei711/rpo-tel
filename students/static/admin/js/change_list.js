document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll("tbody > tr");
    rows.forEach(row => {
      // done_tel が True の行は該当セルに .call-empty.done を付与
      const doneTelImg = row.querySelector("td.field-done_tel img");
      const done = doneTelImg && doneTelImg.alt === "True";
      if (done) {
        ["first_call_date","second_call_date","third_call_date"].forEach(fn => {
          const cell = row.querySelector(`td.field-${fn}`);
          if (cell && (cell.textContent.trim() === "" || cell.textContent.trim() === "-")) {
            cell.classList.add("call-empty","done");
          }
        });
      }
    });
  });
