const FLASH_SUCCESS_KEY = "rhflow.flash.success";

export function setFlashSuccess(message: string) {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(FLASH_SUCCESS_KEY, message);
}

export function takeFlashSuccess(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const message = window.sessionStorage.getItem(FLASH_SUCCESS_KEY);
  if (!message) {
    return null;
  }
  window.sessionStorage.removeItem(FLASH_SUCCESS_KEY);
  return message;
}
