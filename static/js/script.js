function addData() {
  var data = document.getElementById("dataInput").value;
  if (data != "") {
    fetch('/add_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({data: data})
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(json) {
      location.reload();
    })
    .catch(function(error) {
      console.log(error);
    });
  }
}

function gotoProduct() { 
  window.location.href = '/product';
}

function gotoFirstPage() { 
  window.location.href = '/';
}