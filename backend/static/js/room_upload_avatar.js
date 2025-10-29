// 上传头像
document.getElementById('upload-avatar-btn').addEventListener('click', function () {
    // 优先使用common.js中的函数上传头像
    if (typeof uploadAvatar === 'function') {
        uploadAvatar(socket, user_id, username);
    } else {
        // 如果common.js中的函数不可用，使用原有的上传逻辑
        console.log('点击上传头像按钮');
        const fileInput = document.getElementById('avatar-upload');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            console.log('选择的文件:', file);
            const formData = new FormData();
            formData.append('file', file);

            console.log('Socket状态:', socket ? '已连接' : '未连接');
            console.log('User ID:', user_id);

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
                    if (data.avatar_url) {
                        // 添加时间戳防止浏览器缓存
                        const timestamp = new Date().getTime();
                        const avatarUrlWithTimestamp = data.avatar_url.includes('?')
                            ? `${data.avatar_url}&t=${timestamp}`
                            : `${data.avatar_url}?t=${timestamp}`;

                        // 更新预览
                        document.getElementById('avatar-preview').src = avatarUrlWithTimestamp;

                        // 设置头像
                        selectedAvatarUrl = avatarUrlWithTimestamp;
                        avatarSelected = true;

                        // 清除其他选中状态
                        document.querySelectorAll('.avatar-option').forEach(option => {
                            option.classList.remove('selected');
                            if (option.querySelector('img')) {
                                option.querySelector('img').style.border = 'none';
                            }
                        });

                        // 立即调用setAvatar更新用户头像
                        console.log('调用setAvatar函数更新头像');
                        setAvatar(avatarUrlWithTimestamp);

                        // 使用common.js中的函数保存用户信息
                        if (typeof localStorage !== 'undefined' && getCurrentUser && saveCurrentUser && createUserObject) {
                            // 获取当前用户信息
                            const currentUser = getCurrentUser() || {};
                            // 创建更新后的用户对象
                            const updatedUser = createUserObject(
                                currentUser.username || username || '',
                                avatarUrlWithTimestamp,
                                currentUser.user_id || user_id
                            );
                            // 保存到localStorage
                            saveCurrentUser(updatedUser);
                        }
                        alert('头像上传成功');
                    } else {
                        alert('头像上传失败: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('上传头像时发生错误:', error);
                    alert('头像上传失败: ' + error.message);
                });
        } else {
            alert('请选择一个文件');
        }
    }
});