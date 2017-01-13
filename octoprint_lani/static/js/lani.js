const STATUS_URL = 'http://localhost:3000/octoprint_instances/';

window.addEventListener('load', function() {
  const laniTab = document.getElementById('lani');
  const laniReload = document.getElementById('lani-check');
  const laniLink = document.getElementById('lani-link');
  const laniInfo = document.getElementById('lani-info');
  const laniPrintCenterName = document.getElementById('lani-pc-name');

  function checkStatus() {
    laniReload.disabled = true;

    $.ajax({
      type: 'GET',
      url: laniTab.dataset.instanceEndpoint,
      crossDomain: true,
      error: function(jqXHR, statusText) {
        laniReload.disabled = false;
      },
      statusCode: {
        200: function(data) {
          laniReload.style.display = 'none';
          laniLink.style.display = 'none';

          laniPrintCenterName.textContent = data.printCenter.name;
          laniInfo.style.display = 'inline';
        },
        404: function() {
          laniReload.style.display = 'none';
        }
      }
    });
  }

  laniReload.addEventListener('click', function(e) {
    checkStatus();
  });

  checkStatus();
});
