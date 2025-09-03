# pyenv 初始化（确保 pyenv 正常工作） export PYENV_ROOT="$HOME/.pyenv" 
export PATH="$PYENV_ROOT/bin:$PATH" eval "$(pyenv init -)"

# 可选：为 Intel Mac 添加 Homebrew 路径 export PATH="/usr/local/bin:$PATH"
# 安全的 p3 别名（指向 pyenv 管理的 python3.10）"

#alias p3='/Users/ink/.pyenv/versions/3.10.13/bin/python'
#alias p3='python3.10'
#alias pip3='pip3.10'

# 防止 python3/pip 被别名劫持
unalias python3 2>/dev/null || true
unalias pip     2>/dev/null || true
unalias pip3    2>/dev/null || true  # ✅ 加上这一行！
