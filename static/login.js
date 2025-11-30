async function populateSelect() {
    const sel = document.getElementById('user-select')
    sel.innerHTML = ''

    try {
        const response = await fetch('/users')
        if (!response.ok) {
            throw new Error('Network response was not ok')
        }

        const users = await response.json()
        console.log(users)
        users.forEach(user => {
            const option = document.createElement('option')
            option.value = user.User_ID
            option.textContent = user.Username
            console.log(user.Username)
            sel.appendChild(option)
        })
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error)

    }
}

function doLogin(userObj) {
    localStorage.setItem('loggedInUser', JSON.stringify(userObj))
    window.location.href = '/profile'
}

window.addEventListener("load", () => {
    populateSelect()

    document.getElementById("login-btn").addEventListener("click", () => {
        const sel = document.getElementById('user-select')
        console.log(sel)
        const user = JSON.parse(sel.value)
        doLogin(user)
    })
})