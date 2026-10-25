// The order page: fetch a price and show it.
async function showPrice(orderId, customerId) {
  const res = await fetch(`/price?order=${orderId}&customer=${customerId}`);
  const body = await res.json();
  document.querySelector("#total").textContent = body.total.toFixed(2);
}

function onSubmit(event) {
  event.preventDefault();
  const form = event.target;
  showPrice(form.order.value, form.customer.value);
}

document.querySelector("#price-form").addEventListener("submit", onSubmit);
