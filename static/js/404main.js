const button = document.querySelector('.redirect-btn');

const mousehover = () => {
    anime({
        targets: button,
        width: '75%',
        scale: {
            delay: 800,
            value: 1.5
        },
        duration: 1000
    })
}

button.addEventListener('mouseover', mousehover)

const mouseleave = () => {
    anime({
        targets: button,
        width: '50%',
        scale: {
            delay: 400,
            value: 1
        },
        duration: 1000
    })
}

button.addEventListener('mouseleave', mouseleave)


