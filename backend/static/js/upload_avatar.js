
// 本地文件变量
let selectedAvatarFile = null;

function initAvatarUpload() {
    // 获取现有的文件输入框，使用lobbyCommon中的常量
    const avatarUploadInput = document.getElementById(lobbyCommon.ID_AVATAR_UPLOAD_FILE);
    if (avatarUploadInput) {
        // 监听文件选择变化事件
        avatarUploadInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                selectedAvatarFile = this.files[0];
                console.log('已选择文件:', selectedAvatarFile.name);
                
                // 预览文件
                const reader = new FileReader();
                reader.onload = function(e) {
                    // 使用lobbyCommon中的函数设置预览头像
                    lobbyCommon.setPreviewAvatar(e.target.result);
                };
                reader.readAsDataURL(selectedAvatarFile);
            }
        });
    }
    
    // 获取并绑定上传按钮事件，使用lobbyCommon中的常量
    const uploadBtn = document.getElementById(lobbyCommon.ID_UPLOAD_AVATAR_BTN);
    if (uploadBtn) {
        uploadBtn.addEventListener("click", function () {
            if (!selectedAvatarFile) {
                alert('请先选择一个文件');
                return;
            }
            
            // 直接使用已选择的文件输入框
            uploadAvatar(avatarUploadInput);
        });
    }
}


/**
 * 上传头像
 * @param {HTMLInputElement} fileInputDOM - 包含文件的文件输入DOM元素
 */
function uploadAvatar(fileInputDOM) {
    console.log('点击上传头像按钮');;
    if (!fileInputDOM || fileInputDOM.files.length === 0) {
        alert('请选择一个文件');
        return;
    }

    const file = fileInputDOM.files[0];
    console.log('上传的文件:', file);
    const formData = new FormData();
    formData.append('file', file);

    // 上传文件
    console.log('开始上传文件到 /upload_avatar');
    fetch('/upload_avatar', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            console.log('上传响应状态:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP错误! 状态码: ${response.status}`);
            }
            return response.json().catch(err => {
                console.error('解析JSON响应失败:', err);
                // 尝试获取原始文本
                return response.text().then(text => {
                    console.log('原始响应文本:', text);
                    throw new Error('服务器返回了非JSON响应');
                });
            });
        })
        .then(data => {
            console.log('上传成功，服务器返回:', data);
            if (data[ServerDataKey.AvatarURL]) {
                // 使用可能的头像URL字段
                const avatarUrl = data[ServerDataKey.AvatarURL];
                onUploadAvatarSuccess(avatarUrl);
                console.log('头像上传成功');
            } else {
                alert('头像上传失败: ' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            console.error('上传头像时发生错误:', error);
            alert('头像上传失败: ' + error.message);
        });
}


function onUploadAvatarSuccess(avatarUrl) {
    const avatarUrlWithTimestamp = lobbyCommon.getAvatarUrlWithTimestamp(avatarUrl);

    // 使用lobbyCommon中的函数设置预览头像
    lobbyCommon.setPreviewAvatar(avatarUrlWithTimestamp);

    // 使用lobbyCommon中的函数清除选中状态
    lobbyCommon.clearAvatarSelect();
}