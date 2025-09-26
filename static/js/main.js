import { generateTimeOptions, populateSelect } from "./time.js";

function InitElements() {
  return {
    startSelect: document.getElementById("start-time"),
    endSelect:   document.getElementById("end-time"),
  };
}

document.addEventListener("DOMContentLoaded", () => {
  const { startSelect, endSelect, submitBtn } = InitElements();
  populateSelect(startSelect, generateTimeOptions(), "開始時刻");
  populateSelect(endSelect,   generateTimeOptions(), "終了時刻");
});
