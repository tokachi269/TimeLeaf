/**
 * Cookie管理ユーティリティ
 */

/**
 * Cookieに値を設定する
 * @param {string} name - Cookie名
 * @param {string} value - 設定する値
 * @param {number} days - 有効期限（日数）
 */
export function setCookie(name, value, days = 365) {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

/**
 * Cookieから値を取得する
 * @param {string} name - Cookie名
 * @returns {string|null} - Cookie値、存在しない場合はnull
 */
export function getCookie(name) {
  const nameEQ = name + '=';
  const cookies = document.cookie.split(';');
  
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i];
    while (cookie.charAt(0) === ' ') {
      cookie = cookie.substring(1, cookie.length);
    }
    if (cookie.indexOf(nameEQ) === 0) {
      return cookie.substring(nameEQ.length, cookie.length);
    }
  }
  return null;
}

/**
 * Cookieを削除する
 * @param {string} name - Cookie名
 */
export function deleteCookie(name) {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/`;
}

/**
 * バージョン情報をCookieに保存する
 * @param {string} version - バージョン番号
 */
export function saveVersionToCookie(version) {
  setCookie('timeleaf_version', version, 365);
}

/**
 * Cookieからバージョン情報を取得する
 * @returns {string|null} - バージョン番号、存在しない場合はnull
 */
export function getVersionFromCookie() {
  return getCookie('timeleaf_version');
}

/**
 * ユーザーIDをCookieに保存する
 * @param {string} userId - ユーザーID
 */
export function saveUserIdToCookie(userId) {
  setCookie('timeleaf_user_id', userId, 365);
}

/**
 * CookieからユーザーIDを取得する
 * @returns {string|null} - ユーザーID、存在しない場合はnull
 */
export function getUserIdFromCookie() {
  return getCookie('timeleaf_user_id');
}

/**
 * 新規ユーザーかどうかを判定する
 * @returns {boolean} - 新規ユーザーの場合はtrue
 */
export function isNewUser() {
  return !getUserIdFromCookie();
}

/**
 * バージョンが更新されたかどうかを判定する
 * @param {string} currentVersion - 現在のバージョン
 * @returns {boolean} - バージョンが更新された場合はtrue
 */
export function isVersionUpdated(currentVersion) {
  const savedVersion = getVersionFromCookie();
  return !savedVersion || savedVersion !== currentVersion;
}
