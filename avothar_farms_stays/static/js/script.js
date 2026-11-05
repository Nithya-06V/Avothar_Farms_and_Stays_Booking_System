document.addEventListener('DOMContentLoaded', function () {
  const togglePasswordButton = document.getElementById('togglePassword');
  const passwordField = document.getElementById('passwordField');

  if (togglePasswordButton && passwordField) {
    togglePasswordButton.addEventListener('click', function () {
      const isPassword = passwordField.type === 'password';
      passwordField.type = isPassword ? 'text' : 'password';
      togglePasswordButton.textContent = isPassword ? 'Hide' : 'Show';
    });
  }

  const checkIn = document.getElementById('checkIn');
  const checkOut = document.getElementById('checkOut');
  const rooms = document.getElementById('rooms');
  const priceElement = document.getElementById('pricePerNight');
  const nightsValue = document.getElementById('nightsValue');
  const totalAmountValue = document.getElementById('totalAmountValue');

  const updateBookingSummary = function () {
    if (!checkIn || !checkOut || !rooms || !priceElement || !nightsValue || !totalAmountValue) {
      return;
    }

    const start = new Date(checkIn.value);
    const end = new Date(checkOut.value);
    const roomCount = Number(rooms.value || 1);
    const pricePerNight = Number(priceElement.textContent || 0);

    if (checkIn.value && checkOut.value && end > start) {
      const diff = (end - start) / (1000 * 60 * 60 * 24);
      const total = pricePerNight * diff * roomCount;
      nightsValue.textContent = diff;
      totalAmountValue.textContent = total.toLocaleString('en-IN');
    } else {
      nightsValue.textContent = '0';
      totalAmountValue.textContent = '0';
    }
  };

  [checkIn, checkOut, rooms].forEach((element) => {
    if (element) {
      element.addEventListener('input', updateBookingSummary);
      element.addEventListener('change', updateBookingSummary);
    }
  });
});
