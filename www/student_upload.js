

// File upload function
(function ($) {
  $.fn.uploader = function (options) {
    var settings = $.extend(
      {
        MessageAreaText: "No files selected.",
        MessageAreaTextWithFiles: "File List:",
        DefaultErrorMessage: "Unable to open this file.",
        BadTypeErrorMessage: "We cannot accept this file type at this time.",
        acceptedFileTypes: [
          "pdf",
          "jpg",
          "gif",
          "jpeg",
          "bmp",
          "tif",
          "tiff",
          "png",
          "xps",
          "doc",
          "docx",
          "fax",
          "wmp",
          "ico",
          "txt",
          "cs",
          "csv",
          "rtf",
          "xls",
          "xlsx"
        ]
      },
      options
    );

    var uploadId = 1;
    //update the messaging
    $(".file-uploader__message-area p").text(
      options.MessageAreaText || settings.MessageAreaText
    );

    //create and add the file list and the hidden input list
    var fileList = $('<ul class="file-list"></ul>');
    var hiddenInputs = $('<div class="hidden-inputs hidden"></div>');
    $(".file-uploader__message-area").after(fileList);
    $(".file-list").after(hiddenInputs);

    //when choosing a file, add the name to the list and copy the file input into the hidden inputs
    $(".file-chooser__input").on("change", function () {
      var files = document.querySelector(".file-chooser__input").files;

      for (var i = 0; i < files.length; i++) {
        console.log(files[i]);

        var file = files[i];
        var fileName = file.name.match(/([^\\\/]+)$/)[0];

        //clear any error condition
        $(".file-chooser").removeClass("error");
        $(".error-message").remove();

        //validate the file
        var check = checkFile(fileName);
        if (check === "valid") {
          // move the 'real' one to hidden list
          $(".hidden-inputs").append($(".file-chooser__input"));

          //insert a clone after the hiddens (copy the event handlers too)
          $(".file-chooser").append(
            $(".file-chooser__input").clone({ withDataAndEvents: true })
          );

          //add the name and a remove button to the file-list
          $(".file-list").append(
            '<li style="display: none;"><span class="file-list__name">' +
              fileName +
              '</span><button class="removal-button" data-uploadid="' +
              uploadId +
              '"></button></li>'
          );
          $(".file-list").find("li:last").show(800);

          //removal button handler
          $(".removal-button").on("click", function (e) {
            e.preventDefault();

            //remove the corresponding hidden input
            $(
              '.hidden-inputs input[data-uploadid="' +
                $(this).data("uploadid") +
                '"]'
            ).remove();

            //remove the name from file-list that corresponds to the button clicked
            $(this)
              .parent()
              .hide("puff")
              .delay(10)
              .queue(function () {
                $(this).remove();
              });

            //if the list is now empty, change the text back
            if ($(".file-list li").length === 0) {
              $(".file-uploader__message-area").text(
                options.MessageAreaText || settings.MessageAreaText
              );
            }
          });

          //so the event handler works on the new "real" one
          $(".hidden-inputs .file-chooser__input")
            .removeClass("file-chooser__input")
            .attr("data-uploadId", uploadId);

          //update the message area
          $(".file-uploader__message-area").text(
            options.MessageAreaTextWithFiles ||
              settings.MessageAreaTextWithFiles
          );

          uploadId++;
        } else {
          //indicate that the file is not ok
          $(".file-chooser").addClass("error");
          var errorText =
            options.DefaultErrorMessage || settings.DefaultErrorMessage;

          if (check === "badFileName") {
            errorText =
              options.BadTypeErrorMessage || settings.BadTypeErrorMessage;
          }

          $(".file-chooser__input").after(
            '<p class="error-message">' + errorText + "</p>"
          );
        }
      }
    });

    var checkFile = function (fileName) {
      var accepted = "invalid",
        acceptedFileTypes =
          this.acceptedFileTypes || settings.acceptedFileTypes,
        regex;

      for (var i = 0; i < acceptedFileTypes.length; i++) {
        regex = new RegExp("\\." + acceptedFileTypes[i] + "$", "i");

        if (regex.test(fileName)) {
          accepted = "valid";
          break;
        } else {
          accepted = "badFileName";
        }
      }

      return accepted;
    };
  };
})($);



(function ($) {
  $(document).ready(function () {
    
    $(".fileUploader").uploader({
      MessageAreaText: "No files selected. Please select a file."
    });
    
    submit()
    resetButton()
    removeNotification()
    autoRemoveNotification()
    
    var ID
    var way = 0
    var queue = []
    var fullStock = 10
    var speedCloseNoti = 5000
    
    
    function submit() {  
      var button = $('#send')
      
      button.on('click', function () {
        if(!way) {
          var title = $('#title')
          var email  = $('#email')
          var attachments = $(".file-chooser__input")
          var files = document.querySelector(".file-chooser__input").files;
          var currentdate = new Date(); 
          var datetime = currentdate.getDate() + "/" + 
                         (currentdate.getMonth()+1)  + "/" +
                         currentdate.getFullYear() + "_"  +
                         currentdate.getHours() + ":" +
                         currentdate.getMinutes() + ":" +
                         currentdate.getSeconds();
          var attachmentsArr = []
          
          for(var i = 0; i < attachments.length; i++) {
            attachmentsArr.push({url: $(attachments[i]).attr('rel')})
          }
          
          var newStock = {
            title: title.val(),
            email: email.val(),
            attachments: files,
            datetime: datetime,
            type: 1
          }
          
          console.log(newStock)
          
          saveToQueue(newStock)
          // Figure out how to make this work
          cloudConnect(newStock)
        }
      })
    }
    
    function removeNotification() {
      var close = $('.notification')
      close.on('click', 'span', function () {
        var parent = $(this).parent()
        parent.fadeOut(5000)
        setTimeout(function() {
          parent.remove()
        }, 5000)
      })
    }
    
    function autoRemoveNotification() {
      setInterval(function() {
        var notification = $('.notification')
        var notiPage = $(notification).children('.btn')
        var noti = $(notiPage[0])
        
        setTimeout(function () {
          setTimeout(function () {
           noti.remove()
          }, speedCloseNoti)
          noti.fadeOut(speedCloseNoti)
        }, speedCloseNoti)
      }, speedCloseNoti)
    }
    
    function resetButton() {
      var resetbtn = $('#reset')
      resetbtn.on('click', function () {
        reset()
      })
    }
    
    // helpers
    function saveToQueue(stock) {
      var notification = $('.notification')
      var check = 0
      var emails = ["@teachinglab.org", "@schools.nyc.gov", "@rcsdk12.org"]
      var email = document.getElementById("email").value
      
      if(queue.length <= fullStock) {
        if(stock.type == 2) {
            if(!stock.title || !stock.message) {
              check = 1
            }
        } else if(!stock.title || !stock.email || stock.attachments == 0) {
            check = 3
        } else if (email.includes(emails[0]) === false && email.includes(emails[1]) === false && email.includes(emails[2]) === false) {
          check = 2
        }
        
        if (check === 2) {
        notification.append('<div class="error btn"><p><strong>Error:</strong> Please enter a valid email.</p><span><i class=\"fa fa-times\" aria-hidden=\"true\"></i></span></div>')
      } else if(check === 3) {
          notification.append('<div class="error btn"><p><strong>Error:</strong> Please fill in the form.</p><span><i class=\"fa fa-times\" aria-hidden=\"true\"></i></span></div>')
        } else {
          notification.append('<div class="success btn"><p><strong>Success:</strong> '+ 'file' +' is submitted.</p><span><i class=\"fa fa-times\" aria-hidden=\"true\"></i></span></div>')
          queue.push(stock)
          reset()
        }
      } else {
        notification.append('<div class="error btn"><p><strong>Error:</strong> Please waiting a queue.</p><span><i class=\"fa fa-times\" aria-hidden=\"true\"></i></span></div>')
      }
    }
    
    
    function reset() {
      
      $('#title').val('')
      $('#email').val('')
      
      var attachments = $('.attachments .img')
      for(var i = 0; i < attachments.length; i++) {
        $(attachments)[i].remove()
      }
    }
    
    
    
    
    
    
    
  })
})(jQuery)