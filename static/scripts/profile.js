const uploadPictureModal = document.querySelector('#uploadPictureModal');

uploadPictureModal.addEventListener('show.bs.modal', function (e) {
    const btn = e.relatedTarget;
    const imgUrl = btn.getAttribute('data-bs-imgUrl');
})