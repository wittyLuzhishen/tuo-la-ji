// 常量定义
const presetAvatars = [
    "/static/avatars/default.svg",
    "/static/avatars/preset1.svg",
    "/static/avatars/preset2.svg",
    "/static/avatars/preset3.svg",
    "/static/avatars/preset4.svg",
    "/static/avatars/tuolaji.png",
];
// 房间列表相关常量
const ID_ROOM_LIST_TBODY = "room-list-tbody";
const ID_NO_ROOMS_MESSAGE = "no-rooms-message";
const CLASS_JOIN_ROOM_BTN = "join-room-btn";
const ID_USER_AVATAR = "user-avatar";
const ID_USERNAME_INPUT = "username-input";
const ID_USER_INFO_SETTING_MODAL = "user-setup-modal";
const ID_CONFIRM_USER_INFO_UPDATE_BTN = "confirm-user-setup";
const ID_CANCEL_USER_INFO_UPDATE_BTN = "cancel-user-setup";
const ID_USERNAME_ERROR = "username-error";
const ID_USERNAME_DISPLAY = "username-display";
const ID_REFRESH_ROOM_LIST_BTN = "refresh-room-list-btn";


const GAME_STATUS_PLAYING = 'playing';
const GAME_STATUS_WAITING = 'waiting';


// 全局变量
let socket = null;
let roomList = [];
let selectedAvatarUrl = "/static/avatars/default.svg";
let avatarSelected = false;
let userInfoSet = false; // 标记用户信息是否已设置
let mockMode = false; // 模拟模式，用于没有Socket服务器的情况
let selectedFile = null; // 存储用户选择的文件变量



// 当文档加载完成时执行
window.addEventListener("DOMContentLoaded", function () {
    console.log("大厅页面加载完成");

    // 初始化Socket连接
    initLobbySocket();

    requestRoomList(true);

    // 注册按钮事件
    registerButtonEvents();

    // 添加头像点击事件，用于重新打开设置面板
    const userAvatar = document.getElementById(ID_USER_AVATAR);
    if (userAvatar) {
        userAvatar.addEventListener("click", function () {
            console.log("点击头像，打开用户设置面板");
            showUserInfoSettingModal();
        });
    }

    // 初始化预设头像
    initPresetAvatars();

    // 绑定确认按钮事件
    const confirmBtn = document.getElementById(ID_CONFIRM_USER_INFO_UPDATE_BTN);
    if (confirmBtn) {
        confirmBtn.addEventListener("click", onUpdateUserInfoBtnClicked);
    }

    // 绑定取消按钮事件
    const cancelBtn = document.getElementById(ID_CANCEL_USER_INFO_UPDATE_BTN);
    if (cancelBtn) {
        cancelBtn.addEventListener("click", function () {
            console.log("取消用户设置");
            hideModal(ID_USER_INFO_SETTING_MODAL);
        });
    }

});


/**
 * 初始化大厅Socket连接
 */
function initLobbySocket() {
    console.log("初始化大厅Socket连接");

    // 初始化Socket连接
    socket = initSocketConnection("/", {
        reconnectionAttempts: 3,
        reconnectionDelay: 1000,
    });

    if (socket) {
        // 设置Socket监听器
        setupLobbySocketListeners(socket);
    } else {
        console.warn("Socket初始化失败，尝试通过API获取用户ID");
    }
}


/**
 * 设置大厅Socket监听器
 */
function setupLobbySocketListeners(socket) {
    setupSocketListeners(socket, {
        [ServerMessageType.UserIDAssigned]: function (data) {
            try {
                console.log("用户ID分配:", data);
                // 首先调用common.js中的基础处理函数，确保用户ID正确保存
                receiveUserIDAssigned(data);
                
                let user_id = data[ServerDataKey.UserID] || "";
                let currentUser = getCurrentUser();
                
                // 继续执行大厅特有的用户信息更新逻辑
                saveCurrentUser(createUserInfoObject(
                    currentUser[ClientDataKey.Username] ? currentUser[ClientDataKey.Username] : `${user_id}`,
                    currentUser[ClientDataKey.AvatarURL] ? currentUser[ClientDataKey.AvatarURL] : presetAvatars[0],
                    user_id  // 直接使用服务器分配的用户ID
                ));
                updateUserInfoDisplay();
            } catch (error) {
                console.warn("处理用户ID分配事件时发生错误:", error);
            }
        },
        [ServerMessageType.UserInfoUpdated]: function (data) {
            try {
                console.log("用户信息更新:", data);

                let user_id = data[ServerDataKey.UserID] || "";
                let username = data[ServerDataKey.Username] || "";
                let avatar_url = data[ServerDataKey.AvatarURL] || "";
                saveCurrentUser(createUserInfoObject(username, avatar_url, user_id));

                // 更新用户显示
                updateUserInfoDisplay();
            } catch (error) {
                console.warn("处理用户信息更新事件时发生错误:", error);
            }
        },
        [ServerMessageType.RoomList]: function (data) {
            try {
                console.log("房间列表更新:", data);
                roomList = data[ServerDataKey.RoomList] || [];
                updateRoomList(roomList);
            } catch (error) {
                console.warn("处理房间列表更新事件时发生错误:", error);
            }
        },

    });
}


/**
 * 显示用户设置模态框
 */
function showUserInfoSettingModal() {
    console.log("显示用户设置模态框");

    // 获取当前用户信息并填充表单
    const currentUser = getCurrentUser();
    if (!currentUser) {
        console.warn("当前用户信息为空，无法填充表单");
        return;
    }
    // 填充用户名
    const usernameInput = document.getElementById(ID_USERNAME_INPUT);
    if (usernameInput && currentUser[ClientDataKey.Username]) {
        usernameInput.value = currentUser[ClientDataKey.Username];
    }

    // 填充头像
    setPreviewAvatar(currentUser[ClientDataKey.AvatarURL]);

    // 显示模态框
    showModal(ID_USER_INFO_SETTING_MODAL);
}


/**
 * 初始化预设头像
 */
function initPresetAvatars() {
    const avatarGrid = document.querySelector(lobbyCommon.CLASS_AVATAR_GRID);
    if (!avatarGrid) return;

    presetAvatars.forEach((avatarUrl) => {
        const avatarOption = document.createElement("div");
        avatarOption.className = lobbyCommon.CLASS_AVATAR_OPTION;

        const img = document.createElement("img");
        img.src = avatarUrl;
        img.alt = "头像选项";
        img.style.width = "50px";
        img.style.height = "50px";
        img.style.cursor = "pointer";

        // 如果是默认选中的头像，添加选中状态
        if (avatarUrl === selectedAvatarUrl) {
            lobbyCommon.toggleAvatarSelect(avatarOption, img, true);
        }

        // 添加点击事件
        img.addEventListener("click", function () {
            // 清除其他选中状态
            lobbyCommon.clearAvatarSelect();

            // 设置当前选中状态
            lobbyCommon.toggleAvatarSelect(avatarOption, img, true);

            // 更新选中的头像URL
            selectedAvatarUrl = avatarUrl;
            avatarSelected = true;

            // 更新预览
            lobbyCommon.setPreviewAvatar(avatarUrl);
        });

        avatarOption.appendChild(img);
        avatarGrid.appendChild(avatarOption);
    });
}


/**
 * 验证用户名
 * @param {string} username - 要验证的用户名
 * @returns {Object} 验证结果对象 {valid: boolean, error: string}
 */
function validateUsername(username) {
    // 检查用户名是否为空
    if (!username || username.trim() === '') {
        return { valid: false, error: '用户名不能为空' };
    }

    // 检查用户名长度
    if (username.length < 2 || username.length > 20) {
        return { valid: false, error: '用户名长度应在2-20个字符之间' };
    }

    // 检查用户名格式（只允许字母、数字、中文和常见符号）
    const usernamePattern = /^[\u4e00-\u9fa5a-zA-Z0-9_\-\u00b7\u2022\u2014\u2013\u2010\u002d\u005f]{2,20}$/;
    if (!usernamePattern.test(username)) {
        return { valid: false, error: '用户名只能包含中文、英文、数字和下划线' };
    }

    return { valid: true };
}


function toggleUserInfoUpdateErrorInfo(errorElement, showErrorInfo, errorInfo) {
    if (!errorElement) {
        return;
    }
    if (showErrorInfo) {
        errorElement.textContent = errorInfo;
        errorElement.style.display = "block";
        return;
    } else {
        errorElement.style.display = "none";
    }
}


/**
 * 确认用户设置
 */
function onUpdateUserInfoBtnClicked() {
    console.log("确认用户设置");

    // 获取用户名
    const usernameInput = document.getElementById(ID_USERNAME_INPUT);
    const username = usernameInput ? usernameInput.value.trim() : "";

    // 验证用户名
    const validation = validateUsername(username);
    const errorElement = document.getElementById(ID_USERNAME_ERROR);
    toggleUserInfoUpdateErrorInfo(errorElement, !validation.valid, validation.error);

    // 获取头像
    let avatarUrl = getPreviewAvatarUrl();

    toggleUserInfoUpdateErrorInfo(errorElement, !avatarUrl, "请选择头像");

    // 如果Socket已连接，统一发送更新消息
    if (socket && socket.connected) {
        const cleanAvatarUrl = lobbyCommon.getCleanAvatarUrl(avatarUrl);
        socket.emit(ClientMessageType.SetUserInfo, {
            [ClientDataKey.UserID]: getUserId(),
            [ClientDataKey.Username]: username,
            [ClientDataKey.AvatarURL]: cleanAvatarUrl,
        });
    }

    // 隐藏模态框
    hideModal("user-setup-modal");
}


/**
 * 更新用户显示信息
 */
function updateUserInfoDisplay() {
    try {
        const currentUser = getCurrentUser();
        if (!currentUser) {
            return;
        }
        // 更新用户名显示
        const usernameDisplay = document.getElementById(ID_USERNAME_DISPLAY);
        if (usernameDisplay) {
            usernameDisplay.textContent =
                currentUser[ClientDataKey.Username] || "未知用户";
        }

        // 更新头像显示
        const avatarDisplay = document.getElementById(ID_USER_AVATAR);
        if (avatarDisplay && currentUser[ClientDataKey.AvatarURL]) {
            avatarDisplay.src = lobbyCommon.getAvatarUrlWithTimestamp(
                currentUser[ClientDataKey.AvatarURL]
            );
        }
        // 标记用户信息已设置
        userInfoSet = true;
    } catch (error) {
        console.error("更新用户显示时发生错误:", error);
    }
}


// 添加全局事件监听器，确保在Socket重新连接时也能处理
window.addEventListener("focus", function () {
    // 当窗口重新获得焦点时，可以检查连接状态并更新UI
    if (socket && socket.connected) {
        // 如果用户信息未设置，检查是否需要显示设置面板
        const currentUser = getCurrentUser();
        if (!currentUser) {
            updateUserInfoDisplay();
        }
    }
});


/**
 * 更新房间列表
 */
/**
 * 主动请求房间列表信息
 * 此方法会向服务器发送请求，获取最新的房间列表
 * @param {boolean} showLoading - 是否显示加载提示，默认为true
 */
function requestRoomList(showLoading = true) {
    console.log("请求获取房间列表");

    try {
        // 检查Socket连接状态
        if (!socket || !socket.connected) {
            showToast("错误", "网络连接已断开，请重新连接");
            return false;
        }

        // 如果需要，显示加载提示
        if (showLoading) {
            showToast("提示", "正在获取房间列表，请稍候...");
        }

        // 发送请求房间列表的消息到服务器
        socket.emit(ClientMessageType.GetRoomList, {});

        return true;
    } catch (error) {
        console.error("请求房间列表时发生错误:", error);
        showToast("错误", "获取房间列表失败，请重试");
        return false;
    }
}

/**
 * 更新房间列表
 * @param {Array} roomList - 房间列表数据
 */
function updateRoomList(roomList) {
    console.log("更新房间列表:", roomList);

    // 获取房间列表表格体和无房间提示元素
    const roomListTbody = document.getElementById(ID_ROOM_LIST_TBODY);
    const noRoomsMessage = document.getElementById(ID_NO_ROOMS_MESSAGE);

    if (!roomListTbody || !noRoomsMessage) {
        console.error("房间列表元素未找到");
        return;
    }

    // 清空现有房间列表
    roomListTbody.innerHTML = '';

    // 检查房间列表是否为空
    if (!roomList || roomList.length === 0) {
        // 显示无房间提示
        noRoomsMessage.style.display = "block";
        return;
    }

    // 隐藏无房间提示
    noRoomsMessage.style.display = "none";

    // 遍历房间列表，为每个房间创建行
    roomList.forEach(room => {
        // 创建表格行
        const row = document.createElement("tr");

        // 创建房间名称单元格
        const nameCell = document.createElement("td");
        nameCell.textContent = room[ServerDataKey.RoomName] || "未命名房间";
        row.appendChild(nameCell);

        // 创建房主单元格
        const ownerCell = document.createElement("td");
        ownerCell.textContent = room[ServerDataKey.OwnerName] || "未知房主";
        row.appendChild(ownerCell);

        // 创建玩家数量单元格
        const playerCountCell = document.createElement("td");
        const currentPlayers = room[ServerDataKey.PlayerNumber] || 0;
        const maxPlayers = room[ServerDataKey.Settings][ServerDataKey.MaxPlayerNumber] || 6;
        playerCountCell.textContent = `${currentPlayers}/${maxPlayers}`;
        row.appendChild(playerCountCell);

        // 创建房间状态单元格
        const statusCell = document.createElement("td");
        const statusSpan = document.createElement("span");
        statusSpan.classList.add("badge");

        if (room[ServerDataKey.GameStatus] === GAME_STATUS_PLAYING) {
            statusSpan.classList.add("bg-warning");
            statusSpan.textContent = "游戏中";
        } else if (room[ServerDataKey.GameStatus] === GAME_STATUS_WAITING) {
            statusSpan.classList.add("bg-success");
            statusSpan.textContent = "等待中";
        }

        statusCell.appendChild(statusSpan);
        row.appendChild(statusCell);

        // 创建操作单元格
        const actionCell = document.createElement("td");
        const joinButton = document.createElement("button");
        joinButton.classList.add("btn", "btn-sm", "btn-primary", CLASS_JOIN_ROOM_BTN);
        joinButton.textContent = "加入房间";
        joinButton.setAttribute("data-room-id", room[ServerDataKey.RoomID]);

        // 添加点击事件
        joinButton.addEventListener("click", function () {
            const roomId = this.getAttribute("data-room-id");
            joinRoom(roomId);
        });

        actionCell.appendChild(joinButton);
        row.appendChild(actionCell);

        // 将行添加到表格体
        roomListTbody.appendChild(row);
    });
}


/**
 * 加入房间函数
 * @param {string} roomId - 要加入的房间ID
 */
function registerButtonEvents() {
    console.log("注册按钮事件");

    // 刷新房间列表按钮事件
    const refreshRoomListBtn = document.getElementById(ID_REFRESH_ROOM_LIST_BTN);
    if (refreshRoomListBtn) {
        refreshRoomListBtn.addEventListener("click", function () {
            console.log("点击了刷新房间列表按钮");
            requestRoomList(true);
        });
    }
}

function joinRoom(roomId) {
    console.log("尝试加入房间:", roomId);

    try {
        // 检查Socket连接状态
        if (!socket || !socket.connected) {
            showToast("错误", "网络连接已断开，请重新连接");
            return;
        }

        // 获取当前用户信息
        const currentUser = getCurrentUser();
        if (!currentUser || !currentUser[ClientDataKey.UserID]) {
            showToast("错误", "用户信息未设置，请先设置用户信息");
            // 可以选择自动打开用户设置面板
            return;
        }

        // 发送加入房间的消息到服务器
        socket.emit(ClientMessageType.JoinRoom, {
            [ClientDataKey.RoomID]: roomId,
            [ClientDataKey.UserID]: currentUser[ClientDataKey.UserID]
        });

        // 显示等待提示
        showToast("提示", "正在加入房间，请稍候...");

    } catch (error) {
        console.error("加入房间时发生错误:", error);
        showToast("错误", "加入房间失败，请重试");
    }
}
