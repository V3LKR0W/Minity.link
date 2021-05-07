const div = document.querySelectorAll('.animate');

const animatediv = () => {
    anime({
        targets: div,
        width: '65%',
        scale: {
            delay: 300,
            value: 1.5,
        },
        duration: 2000
    })
}


window.onload = function (){
    animatediv()
}