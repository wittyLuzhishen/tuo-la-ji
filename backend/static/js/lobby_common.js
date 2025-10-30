// 大厅页面通用常量和工具函数
// 此文件包含lobby.js和upload_avatar.js共用的常量和函数

// 头像相关常量
const ID_AVATAR_PREVIEW = "avatar-preview"; // 头像预览图片元素ID
const CLASS_AVATAR_OPTION = "avatar-option"; // 头像选项类名
const CLASS_AVATAR_GRID = ".avatar-grid"; // 头像网格选择器
const ID_AVATAR_UPLOAD_FILE = 'avatar-upload-file'; // 上传头像文件输入框ID
const ID_UPLOAD_AVATAR_BTN = "upload-avatar-btn"; // 上传头像按钮ID

/**
 * 获取预览头像URL
 * @returns {string} 预览头像URL
 */
function getPreviewAvatarUrl() {
    const avatarPreview = document.getElementById(ID_AVATAR_PREVIEW);
    return avatarPreview ? avatarPreview.src : "";
}

/**
 * 设置预览头像
 * @param {string} avatarUrl - 头像URL
 */
function setPreviewAvatar(avatarUrl) {
    const avatarPreview = document.getElementById(ID_AVATAR_PREVIEW);
    if (avatarPreview && avatarUrl) {
        avatarPreview.src = avatarUrl;
    }
}

/**
 * 清除头像选择状态
 */
function clearAvatarSelect() {
    document.querySelectorAll(`.${CLASS_AVATAR_OPTION}`).forEach(option => {
        if (option.querySelector('img')) {
            const imgDOM = option.querySelector('img');
            imgDOM.style.border = "none";
            option.classList.remove("selected");
        }
    });
}

/**
 * 切换头像选择状态
 * @param {HTMLElement} avatarOptionDOM - 头像选项DOM元素
 * @param {HTMLImageElement} imgDOM - 头像图片DOM元素
 * @param {boolean} selected - 是否选中
 */
function toggleAvatarSelect(avatarOptionDOM, imgDOM, selected) {
    if (!selected) {
        imgDOM.style.border = "none";
        avatarOptionDOM.classList.remove("selected");
        return;
    }
    imgDOM.style.border = "2px solid #007bff";
    avatarOptionDOM.classList.add("selected");
}

/**
 * 获取清理后的头像URL（去除时间戳等参数）
 * @param {string} avatarUrl - 原始头像URL
 * @returns {string} 清理后的头像URL
 */
function getCleanAvatarUrl(avatarUrl) {
    if (!avatarUrl) return '';

    try {
        // 解析URL
        const url = new URL(avatarUrl, window.location.origin);

        // 移除时间戳参数
        url.searchParams.delete('t');

        return url.pathname + url.search;
    } catch (error) {
        console.error('清理头像URL时发生错误:', error);
        return avatarUrl;
    }
}

/**
 * 设置头像URL（添加时间戳防止缓存）
 * @param {string} avatarUrl - 头像URL
 * @returns {string} 添加时间戳后的头像URL
 */
function getAvatarUrlWithTimestamp(avatarUrl) {
    if (!avatarUrl) return null;

    // 先获取清理后的URL
    const cleanAvatarUrl = getCleanAvatarUrl(avatarUrl);

    // 添加新的时间戳防止浏览器缓存
    const timestamp = new Date().getTime();
    return cleanAvatarUrl.includes('?')
        ? `${cleanAvatarUrl}&t=${timestamp}`
        : `${cleanAvatarUrl}?t=${timestamp}`;
}


// 定义lobbyCommon全局对象，与common.js保持一致的导出方式
if (typeof window !== 'undefined') {
    // 如果lobbyCommon对象不存在，则创建它
    window.lobbyCommon = window.lobbyCommon || {};
    
    // 将常量和函数暴露到全局对象
    window.lobbyCommon.ID_AVATAR_PREVIEW = ID_AVATAR_PREVIEW;
    window.lobbyCommon.CLASS_AVATAR_OPTION = CLASS_AVATAR_OPTION;
    window.lobbyCommon.CLASS_AVATAR_GRID = CLASS_AVATAR_GRID;
    window.lobbyCommon.ID_AVATAR_UPLOAD_FILE = ID_AVATAR_UPLOAD_FILE;
    window.lobbyCommon.ID_UPLOAD_AVATAR_BTN = ID_UPLOAD_AVATAR_BTN;
    window.lobbyCommon.getPreviewAvatarUrl = getPreviewAvatarUrl;
    window.lobbyCommon.setPreviewAvatar = setPreviewAvatar;
    window.lobbyCommon.clearAvatarSelect = clearAvatarSelect;
    window.lobbyCommon.toggleAvatarSelect = toggleAvatarSelect;
    window.lobbyCommon.getCleanAvatarUrl = getCleanAvatarUrl;
    window.lobbyCommon.getAvatarUrlWithTimestamp = getAvatarUrlWithTimestamp;
}