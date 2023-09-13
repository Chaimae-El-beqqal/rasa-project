// Get the loader element
const loader = document.getElementById("loader");



// Get the progress text element
const progressing = document.getElementById("progress");

const progress = document.getElementById("progr");
let val = 0;

function incrementValue() {
  // Increment val by 5
  val += 5;

  // Update the progress text
  progress.textContent = `${val}%`;

  // Log the current value
  const progressBar = document.querySelector(".progress-fill1");
  progressBar.style.width = `${val}%`;
  console.log(val);

  // Check if val is less than 100
  if (val < 100 && !fetchComplete) {
    // If so, schedule the next increment after 600 milliseconds
    setTimeout(incrementValue, 600);
  } else if (val === 100) {
    val = 0;
  }
}

let fetchComplete = false;

// Function to handle form submission
function handleSubmitForm(formId, url) {
  const form = document.getElementById(formId);

  form.addEventListener("submit", function (event) {
    event.preventDefault();

    // Get the button id
    const btnId = event.submitter.id;

    // Show progress if it s training form
    if (formId === "train-model-form") {
      progressing.style.display = "block";
      // Start the incrementing process
      setTimeout(incrementValue, 5000);
    }
    // Show loader if it s reload form
    if (formId === "reload-model-form") {
      loader.style.display = "block";

    }


    // Send form data using AJAX
    const formData = new FormData(form);

    fetch(url, {
      method: "POST",
      headers: {
        "Custom-Info": btnId,
      },
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        // Hide progress if is   training form
        if (formId == "train-model-form" && data) {
          progressing.style.display = "none";
          console.log(val + 5);
          val=0
        }// Hide loader if is   reload form
        if (formId == "reload-model-form" && data) {
          loader.style.display = "none";

        }

        // Handle the response as needed
        const responseElement = document.getElementById("response");

        // Clear previous success messages
        responseElement.innerHTML = "";

        if (data.success) {
          responseElement.style.display = "block";
          const p = document.createElement("p");
          p.textContent = data.success;
          responseElement.appendChild(p);
          Swal.fire('Success!', data.success, 'success');
          // Clear the upload form if it's successful
          if (formId === "upload-form") {
            form.reset();
          }
        } else if (!data.success) {
          responseElement.style.display = "none";
        }
        // Handle warnings and missing columns
        const warning = document.getElementById("warning");

        // Clear previous warning messages
        warning.innerHTML = "";

        if (data.rapport && typeof data.rapport === 'object') {
          warning.style.display ="block"
          const rapport = data.rapport;
          const ul = document.createElement("ul");

          for (const key in rapport) {
            if (rapport.hasOwnProperty(key)) {
              const value = rapport[key];
              console.log(`${key}:`, value);

              // Create a new list item and set its text content
              const li = document.createElement("li");

              if (key === 'missing columns') {
                const msg = `Please check the following columns:\n ${value.join(', ')}\nand add their corresponding files`;
                li.textContent = `❗ ${key}: ${JSON.stringify(value)}`;
                Swal.fire('Missing Columns!', msg, 'warning');
              }

              // Handle duplicated data or missing data
              if (key === 'duplicated data' || key === "missing data") {
                li.textContent = `❗ we deleted ${key}: \n`;
                const dataValue = rapport[key];
                for (const k in dataValue) {
                  if (dataValue.hasOwnProperty(k)) {
                    const dataArray = dataValue[k]
                    const indexes = dataArray.map(item => item + 2);
                    li.textContent += ` 🔸 ${k}: ${indexes}`;
                  }
                }
              }
              // Append the list item to the unordered list
              ul.appendChild(li);
            }
          }

          // Display warnings
          if (ul.childElementCount > 0) {
            warning.appendChild(ul);
          }
        }else if(!data.warning){
        warning.style.display ="none"
        }

        // Handle model path
        if (data.model_path) {
          console.log(data.model_path);
        }

        // Handle errors
        const errorElt = document.getElementById("error");

        // Clear previous error messages
        errorElt.innerHTML = "";

        if (data.error) {
          errorElt.style.display ="block"
          const msg = JSON.stringify(data.error);
          const p2 = document.createElement("p");
          p2.textContent = "🚨 " + msg;
          errorElt.appendChild(p2);
          Swal.fire('Error!', msg, 'error');
        }else{
                 errorElt.style.display ="none"
        }
      })
      .catch((error) => {
        loader.style.display = "none";
        console.error("Error:", error);
        Swal.fire('Error!', error, 'error');
      });
  });
}

// Call the function for each form
handleSubmitForm("upload-form", "/upload");
handleSubmitForm("train-model-form", "/train");
handleSubmitForm("reload-model-form", "/reload");

WebChat.default.init({
  selector: "#rasa-chat-widget",
  initPayload: "/get_started", // Initial payload for the Rasa chatbot
  socketUrl: "http://localhost:5005",
  customData: { language: "en" }, // Customize as needed
});
