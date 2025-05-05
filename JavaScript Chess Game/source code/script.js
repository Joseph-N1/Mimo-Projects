let main = {
  variables: {
    gameOver: false,
    turn: 'w',
    selectedpiece: '',
    highlighted: [],
    pieces: {
      w_king: {
        position: '5_1',
        img: '&#9812;',
        captured: false,
        moved: false,
        type: 'w_king'
      },
      w_queen: {
        position: '4_1',
        img: '&#9813;',
        captured: false,
        moved: false,
        type: 'w_queen'
      },
      w_bishop1: {
        position: '3_1',
        img: '&#9815;',
        captured: false,
        moved: false,
        type: 'w_bishop'
      },
      w_bishop2: {
        position: '6_1',
        img: '&#9815;',
        captured: false,
        moved: false,
        type: 'w_bishop'
      },
      w_knight1: {
        position: '2_1',
        img: '&#9816;',
        captured: false,
        moved: false,
        type: 'w_knight'
      },
      w_knight2: {
        position: '7_1',
        img: '&#9816;',
        captured: false,
        moved: false,
        type: 'w_knight'
      },
      w_rook1: {
        position: '1_1',
        img: '&#9814;',
        captured: false,
        moved: false,
        type: 'w_rook'
      },
      w_rook2: {
        position: '8_1',
        img: '&#9814;',
        captured: false,
        moved: false,
        type: 'w_rook'
      },
      w_pawn1: {
        position: '1_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn2: {
        position: '2_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn3: {
        position: '3_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn4: {
        position: '4_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn5: {
        position: '5_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn6: {
        position: '6_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn7: {
        position: '7_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      w_pawn8: {
        position: '8_2',
        img: '&#9817;',
        captured: false,
        type: 'w_pawn',
        moved: false
      },
      b_king: {
        position: '5_8',
        img: '&#9818;',
        captured: false,
        moved: false,
        type: 'b_king'
      },
      b_queen: {
        position: '4_8',
        img: '&#9819;',
        captured: false,
        moved: false,
        type: 'b_queen'
      },
      b_bishop1: {
        position: '3_8',
        img: '&#9821;',
        captured: false,
        moved: false,
        type: 'b_bishop'
      },
      b_bishop2: {
        position: '6_8',
        img: '&#9821;',
        captured: false,
        moved: false,
        type: 'b_bishop'
      },
      b_knight1: {
        position: '2_8',
        img: '&#9822;',
        captured: false,
        moved: false,
        type: 'b_knight'
      },
      b_knight2: {
        position: '7_8',
        img: '&#9822;',
        captured: false,
        moved: false,
        type: 'b_knight'
      },
      b_rook1: {
        position: '1_8',
        img: '&#9820;',
        captured: false,
        moved: false,
        type: 'b_rook'
      },
      b_rook2: {
        position: '8_8',
        img: '&#9820;',
        captured: false,
        moved: false,
        type: 'b_rook'
      },
      b_pawn1: {
        position: '1_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn2: {
        position: '2_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn3: {
        position: '3_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn4: {
        position: '4_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn5: {
        position: '5_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn6: {
        position: '6_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn7: {
        position: '7_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      },
      b_pawn8: {
        position: '8_7',
        img: '&#9823;',
        captured: false,
        type: 'b_pawn',
        moved: false
      }
    }
  },

  methods: {
    canCastle: function(color) {
      const rookSide = color === 'w' ? 
        $('#6_1').attr('chess') === 'null' && 
        $('#7_1').attr('chess') === 'null' :
        $('#6_8').attr('chess') === 'null' && 
        $('#7_8').attr('chess') === 'null';
      
      const queenSide = color === 'w' ?
        $('#2_1').attr('chess') === 'null' &&
        $('#3_1').attr('chess') === 'null' &&
        $('#4_1').attr('chess') === 'null' :
        $('#2_8').attr('chess') === 'null' &&
        $('#3_8').attr('chess') === 'null' &&
        $('#4_8').attr('chess') === 'null';
      
      return (rookSide || queenSide) && 
             !main.variables.pieces[`${color}_king`].moved;
    },

    gamesetup: function() {
      $('.gamecell').attr('chess', 'null');
      for (let gamepiece in main.variables.pieces) {
        $('#' + main.variables.pieces[gamepiece].position)
          .html(main.variables.pieces[gamepiece].img)
          .attr('chess', gamepiece);
      }
    },

    moveoptions: function(selectedpiece) {
      let position = {
        x: main.variables.pieces[selectedpiece].position.split('_')[0],
        y: main.variables.pieces[selectedpiece].position.split('_')[1]
      };
    
      if (main.variables.highlighted.length !== 0) {
        main.methods.togglehighlight(main.variables.highlighted);
      }
    
      const startpoint = main.variables.pieces[selectedpiece].position;
      let options = [];
      let coordinates = [];
    
      switch (main.variables.pieces[selectedpiece].type) {
        case 'w_king':
          const canCastleKingside = $('#6_1').attr('chess') === 'null' && 
                                   $('#7_1').attr('chess') === 'null' && 
                                   !main.variables.pieces['w_king'].moved && 
                                   !main.variables.pieces['w_rook2'].moved;
    
          coordinates = [
            { x: 1, y: 1 }, { x: 1, y: 0 }, { x: 1, y: -1 },
            { x: 0, y: -1 }, { x: -1, y: -1 }, { x: -1, y: 0 },
            { x: -1, y: 1 }, { x: 0, y: 1 }
          ];
    
          if (canCastleKingside) {
            coordinates.push({ x: 2, y: 0 });
          }
    
          coordinates = coordinates.map(val => 
            `${parseInt(position.x) + val.x}_${parseInt(position.y) + val.y}`
          );
          break;
    
        case 'b_king':
          const bCanCastleKingside = $('#6_8').attr('chess') === 'null' && 
                                    $('#7_8').attr('chess') === 'null' && 
                                    !main.variables.pieces['b_king'].moved && 
                                    !main.variables.pieces['b_rook2'].moved;
    
          coordinates = [
            { x: 1, y: 1 }, { x: 1, y: 0 }, { x: 1, y: -1 },
            { x: 0, y: -1 }, { x: -1, y: -1 }, { x: -1, y: 0 },
            { x: -1, y: 1 }, { x: 0, y: 1 }
          ];
    
          if (bCanCastleKingside) {
            coordinates.push({ x: 2, y: 0 });
          }
    
          coordinates = coordinates.map(val => 
            `${parseInt(position.x) + val.x}_${parseInt(position.y) + val.y}`
          );
          break;
    
        case 'w_queen':
        case 'b_queen':
          const directions = [
            [{x: 1, y: 1}, {x: 2, y: 2}, {x: 3, y: 3}, {x: 4, y: 4}, 
             {x: 5, y: 5}, {x: 6, y: 6}, {x: 7, y: 7}],
            [{x: 1, y: -1}, {x: 2, y: -2}, {x: 3, y: -3}, {x: 4, y: -4}, 
             {x: 5, y: -5}, {x: 6, y: -6}, {x: 7, y: -7}],
            [{x: -1, y: 1}, {x: -2, y: 2}, {x: -3, y: 3}, {x: -4, y: 4}, 
             {x: -5, y: 5}, {x: -6, y: 6}, {x: -7, y: 7}],
            [{x: -1, y: -1}, {x: -2, y: -2}, {x: -3, y: -3}, {x: -4, y: -4}, 
             {x: -5, y: -5}, {x: -6, y: -6}, {x: -7, y: -7}],
            [{x: 1, y: 0}, {x: 2, y: 0}, {x: 3, y: 0}, {x: 4, y: 0}, 
             {x: 5, y: 0}, {x: 6, y: 0}, {x: 7, y: 0}],
            [{x: 0, y: 1}, {x: 0, y: 2}, {x: 0, y: 3}, {x: 0, y: 4}, 
             {x: 0, y: 5}, {x: 0, y: 6}, {x: 0, y: 7}],
            [{x: -1, y: 0}, {x: -2, y: 0}, {x: -3, y: 0}, {x: -4, y: 0}, 
             {x: -5, y: 0}, {x: -6, y: 0}, {x: -7, y: 0}],
            [{x: 0, y: -1}, {x: 0, y: -2}, {x: 0, y: -3}, {x: 0, y: -4}, 
             {x: 0, y: -5}, {x: 0, y: -6}, {x: 0, y: -7}]
          ];
    
          coordinates = directions.reduce((acc, dir) => {
            const method = main.variables.pieces[selectedpiece].type === 'w_queen' ? 
                          'w_options' : 'b_options';
            return acc.concat(main.methods[method](position, dir));
          }, []);
          break;
    
        case 'w_bishop':
        case 'b_bishop':
          const bishopDirections = [
            [{x: 1, y: 1}, {x: 2, y: 2}, {x: 3, y: 3}, {x: 4, y: 4}, 
             {x: 5, y: 5}, {x: 6, y: 6}, {x: 7, y: 7}],
            [{x: 1, y: -1}, {x: 2, y: -2}, {x: 3, y: -3}, {x: 4, y: -4}, 
             {x: 5, y: -5}, {x: 6, y: -6}, {x: 7, y: -7}],
            [{x: -1, y: 1}, {x: -2, y: 2}, {x: -3, y: 3}, {x: -4, y: 4}, 
             {x: -5, y: 5}, {x: -6, y: 6}, {x: -7, y: 7}],
            [{x: -1, y: -1}, {x: -2, y: -2}, {x: -3, y: -3}, {x: -4, y: -4}, 
             {x: -5, y: -5}, {x: -6, y: -6}, {x: -7, y: -7}]
          ];
    
          coordinates = bishopDirections.reduce((acc, dir) => {
            const method = main.variables.pieces[selectedpiece].type === 'w_bishop' ? 
                          'w_options' : 'b_options';
            return acc.concat(main.methods[method](position, dir));
          }, []);
          break;
    
        case 'w_knight':
        case 'b_knight':
          coordinates = [
            { x: -1, y: 2 }, { x: 1, y: 2 }, { x: 1, y: -2 }, 
            { x: -1, y: -2 }, { x: 2, y: 1 }, { x: 2, y: -1 }, 
            { x: -2, y: -1 }, { x: -2, y: 1 }
          ].map(val => 
            `${parseInt(position.x) + val.x}_${parseInt(position.y) + val.y}`
          );
          break;
    
        case 'w_rook':
        case 'b_rook':
          const rookDirections = [
            [{x: 1, y: 0}, {x: 2, y: 0}, {x: 3, y: 0}, {x: 4, y: 0}, 
             {x: 5, y: 0}, {x: 6, y: 0}, {x: 7, y: 0}],
            [{x: 0, y: 1}, {x: 0, y: 2}, {x: 0, y: 3}, {x: 0, y: 4}, 
             {x: 0, y: 5}, {x: 0, y: 6}, {x: 0, y: 7}],
            [{x: -1, y: 0}, {x: -2, y: 0}, {x: -3, y: 0}, {x: -4, y: 0}, 
             {x: -5, y: 0}, {x: -6, y: 0}, {x: -7, y: 0}],
            [{x: 0, y: -1}, {x: 0, y: -2}, {x: 0, y: -3}, {x: 0, y: -4}, 
             {x: 0, y: -5}, {x: 0, y: -6}, {x: 0, y: -7}]
          ];
    
          coordinates = rookDirections.reduce((acc, dir) => {
            const method = main.variables.pieces[selectedpiece].type === 'w_rook' ? 
                          'w_options' : 'b_options';
            return acc.concat(main.methods[method](position, dir));
          }, []);
          break;
    
        case 'w_pawn':
          if (!main.variables.pieces[selectedpiece].moved) {
            coordinates = [
              { x: 0, y: 1 }, { x: 0, y: 2 },
              { x: 1, y: 1 }, { x: -1, y: 1 }
            ];
          } else {
            coordinates = [
              { x: 0, y: 1 },
              { x: 1, y: 1 }, { x: -1, y: 1 }
            ];
          }
          coordinates = coordinates.map(val => 
            `${parseInt(position.x) + val.x}_${parseInt(position.y) + val.y}`
          );
          break;
    
        case 'b_pawn':
          if (!main.variables.pieces[selectedpiece].moved) {
            coordinates = [
              { x: 0, y: -1 }, { x: 0, y: -2 },
              { x: 1, y: -1 }, { x: -1, y: -1 }
            ];
          } else {
            coordinates = [
              { x: 0, y: -1 },
              { x: 1, y: -1 }, { x: -1, y: -1 }
            ];
          }
          coordinates = coordinates.map(val => 
            `${parseInt(position.x) + val.x}_${parseInt(position.y) + val.y}`
          );
          break;
      }
    
      options = main.methods.options(startpoint, coordinates, 
               main.variables.pieces[selectedpiece].type);
    
      main.variables.highlighted = [...options];
      main.methods.togglehighlight(options);
    },

    options: function(startpoint, coordinates, piecetype) {
      coordinates = coordinates.filter(val => {
        let pos = { x: 0, y: 0 };
        pos.x = parseInt(val.split('_')[0]);
        pos.y = parseInt(val.split('_')[1]);

        if (!(pos.x < 1) && !(pos.x > 8) && !(pos.y < 1) && !(pos.y > 8)) {
          return val;
        }
      });

      switch (piecetype) {
        case 'w_king':
          coordinates = coordinates.filter(val => {
            return ($('#' + val).attr('chess') == 'null' || ($('#' + val).attr('chess')).slice(0,1) == 'b');
          });
          break;
        case 'b_king':
          coordinates = coordinates.filter(val => {
            return ($('#' + val).attr('chess') == 'null' || ($('#' + val).attr('chess')).slice(0,1) == 'w');
          });
          break;
        case 'w_knight':
          coordinates = coordinates.filter(val => {
            return ($('#' + val).attr('chess') == 'null' || ($('#' + val).attr('chess')).slice(0,1) == 'b');
          });
          break;
        case 'b_knight':
          coordinates = coordinates.filter(val => {
            return ($('#' + val).attr('chess') == 'null' || ($('#' + val).attr('chess')).slice(0,1) == 'w');
          });
          break;
        case 'w_pawn':
          coordinates = coordinates.filter(val => {
            let sp = { x: 0, y: 0 };
            let coordinate = val.split('_');

            sp.x = startpoint.split('_')[0];
            sp.y = startpoint.split('_')[1];
            
            if (coordinate[0] < sp.x || coordinate[0] > sp.x) {
              return ($('#' + val).attr('chess') != 'null' && ($('#' + val).attr('chess')).slice(0,1) == 'b');
            } else {
              if (coordinate[1] == (parseInt(sp.y) + 2) && $('#' + sp.x + '_' + (parseInt(sp.y) + 1)).attr('chess') != 'null') {
                // Skip if blocked on first move
              } else {
                return ($('#' + val).attr('chess') == 'null');
              }
            }
          });
          break;
        case 'b_pawn':
          coordinates = coordinates.filter(val => {
            let sp = { x: 0, y: 0 };
            let coordinate = val.split('_');

            sp.x = startpoint.split('_')[0];
            sp.y = startpoint.split('_')[1];
            
            if (coordinate[0] < sp.x || coordinate[0] > sp.x) {
              return ($('#' + val).attr('chess') != 'null' && ($('#' + val).attr('chess')).slice(0,1) == 'w');
            } else {
              if (coordinate[1] == (parseInt(sp.y) - 2) && $('#' + sp.x + '_' + (parseInt(sp.y) - 1)).attr('chess') != 'null') {
                // Skip if blocked on first move
              } else {
                return ($('#' + val).attr('chess') == 'null');
              }
            }
          });
          break;
      }
      return coordinates;
    },

    w_options: function(position, coordinates) {
      let flag = false;
      
      coordinates = coordinates.map(function(val) {
          return (parseInt(position.x) + parseInt(val.x)) + '_' + (parseInt(position.y) + parseInt(val.y));
        }).filter(val => {
          let pos = { x: 0, y: 0 };
          pos.x = parseInt(val.split('_')[0]);
          pos.y = parseInt(val.split('_')[1]);
  
          if (!(pos.x < 1) && !(pos.x > 8) && !(pos.y < 1) && !(pos.y > 8)) {
            return val;
          }
        }).filter(val => {
          if (flag == false) {
            if ($('#' + val).attr('chess') == 'null') {
              return val;
            } else if (($('#' + val).attr('chess')).slice(0,1) == 'b') {
              flag = true;
              return val;
            } else if (($('#' + val).attr('chess')).slice(0,1) == 'w') {
              flag = true;
            }
          }
        });

      return coordinates;
    },

    b_options: function(position, coordinates) {
      let flag = false;
      
      coordinates = coordinates.map(function(val) {
          return (parseInt(position.x) + parseInt(val.x)) + '_' + (parseInt(position.y) + parseInt(val.y));
        }).filter(val => {
          let pos = { x: 0, y: 0 };
          pos.x = parseInt(val.split('_')[0]);
          pos.y = parseInt(val.split('_')[1]);
  
          if (!(pos.x < 1) && !(pos.x > 8) && !(pos.y < 1) && !(pos.y > 8)) {
            return val;
          }
        }).filter(val => {
          if (flag == false) {
            if ($('#' + val).attr('chess') == 'null') {
              return val;
            } else if (($('#' + val).attr('chess')).slice(0,1) == 'w') {
              flag = true;
              return val;
            } else if (($('#' + val).attr('chess')).slice(0,1) == 'b') {
              flag = true;
            }
          }
        });

      return coordinates;
    },

    capture: function(target) {
      let selectedpiece = {
        name: $('#' + main.variables.selectedpiece).attr('chess'),
        id: main.variables.selectedpiece
      };
    
      $('#' + target.id).html(main.variables.pieces[selectedpiece.name].img)
                       .attr('chess', selectedpiece.name);
    
      $('#' + selectedpiece.id).html('').attr('chess', 'null');
    
      main.variables.pieces[selectedpiece.name].position = target.id;
      main.variables.pieces[selectedpiece.name].moved = true;
      main.variables.pieces[target.name].captured = true;
    
      if (target.name === 'w_king' || target.name === 'b_king') {
        main.variables.gameOver = true;
        const winner = target.name.startsWith('w') ? 'Black' : 'White';
        $('#turn').html(`Game Over! ${winner} wins!`).css('background', '#ff4444');
        $('.gamecell').off('click');
      }
    },

    move: function(target) {
      let selectedpiece = $('#' + main.variables.selectedpiece).attr('chess');
    
      $('#' + target.id).html(main.variables.pieces[selectedpiece].img)
                        .attr('chess', selectedpiece);
      
      $('#' + main.variables.selectedpiece).html('').attr('chess', 'null');
      
      main.variables.pieces[selectedpiece].position = target.id;
      main.variables.pieces[selectedpiece].moved = true;
    
      if ((main.variables.pieces[selectedpiece].type === 'w_pawn' && target.id.split('_')[1] === '8') ||
         (main.variables.pieces[selectedpiece].type === 'b_pawn' && target.id.split('_')[1] === '1')) {
        this.promotePawn(target.id, selectedpiece);
      }
    },
    
    promotePawn: function(position, piece) {
      const color = piece.startsWith('w') ? 'w' : 'b';
      const newPieceName = `${color}_queen_${Date.now()}`;
      
      main.variables.pieces[newPieceName] = {
          position: position,
          img: color === 'w' ? '&#9813;' : '&#9819;',
          captured: false,
          moved: true,
          type: `${color}_queen`
      };
      
      delete main.variables.pieces[piece];
      $('#' + position)
          .html(main.variables.pieces[newPieceName].img)
          .attr('chess', newPieceName);
    },
  
    endturn: function() {
      if (main.variables.turn === 'w') {
        main.variables.turn = 'b';
        $('#turn').html("It's Black's Turn");
      } else {
        main.variables.turn = 'w';
        $('#turn').html("It's White's Turn");
      }
      
      main.methods.togglehighlight(main.variables.highlighted);
      main.variables.highlighted = [];
      main.variables.selectedpiece = '';
      
      $('#turn').addClass('turnhighlight');
      setTimeout(() => $('#turn').removeClass('turnhighlight'), 1500);
    },

    togglehighlight: function(options) {
      options.forEach(function(element) {
        $('#' + element).toggleClass("green shake-little neongreen_txt");
      });
    }
  }
};

$(document).ready(function() {
  main.methods.gamesetup();

  $('.gamecell').click(function(e) {
    if (main.variables.gameOver) return;

    var selectedpiece = {
      name: '',
      id: main.variables.selectedpiece
    };

    if (main.variables.selectedpiece == '') {
      selectedpiece.name = $('#' + e.target.id).attr('chess');
    } else {
      selectedpiece.name = $('#' + main.variables.selectedpiece).attr('chess');
    }

    var target = {
      name: $(this).attr('chess'),
      id: e.target.id
    };

    if (main.variables.selectedpiece == '' && target.name.slice(0,1) == main.variables.turn) {
      main.variables.selectedpiece = e.target.id;
      main.methods.moveoptions($(this).attr('chess'));
    } 
    else if (main.variables.selectedpiece !='' && target.name == 'null') {
      if (selectedpiece.name === 'w_king' || selectedpiece.name === 'b_king') {
        if (selectedpiece.name === 'w_king' && 
            !main.variables.pieces['w_king'].moved && 
            !main.variables.pieces['w_rook2'].moved &&
            target.id === '7_1' &&
            $('#6_1').attr('chess') === 'null' && 
            $('#7_1').attr('chess') === 'null') {
            
            main.variables.pieces['w_king'].position = '7_1';
            main.variables.pieces['w_king'].moved = true;
            $('#5_1').html('').attr('chess', 'null');
            $('#7_1').html(main.variables.pieces['w_king'].img)
                    .attr('chess', 'w_king');
            
            main.variables.pieces['w_rook2'].position = '6_1';
            main.variables.pieces['w_rook2'].moved = true;
            $('#8_1').html('').attr('chess', 'null');
            $('#6_1').html(main.variables.pieces['w_rook2'].img)
                    .attr('chess', 'w_rook2');
            
            main.methods.endturn();
        } 
        else if (selectedpiece.name === 'b_king' && 
                 !main.variables.pieces['b_king'].moved && 
                 !main.variables.pieces['b_rook2'].moved &&
                 target.id === '7_8' &&
                 $('#6_8').attr('chess') === 'null' && 
                 $('#7_8').attr('chess') === 'null') {
            
            main.variables.pieces['b_king'].position = '7_8';
            main.variables.pieces['b_king'].moved = true;
            $('#5_8').html('').attr('chess', 'null');
            $('#7_8').html(main.variables.pieces['b_king'].img)
                    .attr('chess', 'b_king');
            
            main.variables.pieces['b_rook2'].position = '6_8';
            main.variables.pieces['b_rook2'].moved = true;
            $('#8_8').html('').attr('chess', 'null');
            $('#6_8').html(main.variables.pieces['b_rook2'].img)
                    .attr('chess', 'b_rook2');
            
            main.methods.endturn();
        }
        else if (selectedpiece.name === 'w_king' && 
                 !main.variables.pieces['w_king'].moved && 
                 !main.variables.pieces['w_rook1'].moved &&
                 target.id === '3_1' &&
                 $('#2_1').attr('chess') === 'null' && 
                 $('#3_1').attr('chess') === 'null' &&
                 $('#4_1').attr('chess') === 'null') {
            
            main.variables.pieces['w_king'].position = '3_1';
            main.variables.pieces['w_king'].moved = true;
            $('#5_1').html('').attr('chess', 'null');
            $('#3_1').html(main.variables.pieces['w_king'].img)
                    .attr('chess', 'w_king');
            
            main.variables.pieces['w_rook1'].position = '4_1';
            main.variables.pieces['w_rook1'].moved = true;
            $('#1_1').html('').attr('chess', 'null');
            $('#4_1').html(main.variables.pieces['w_rook1'].img)
                    .attr('chess', 'w_rook1');
            
            main.methods.endturn();
        }
        else if (selectedpiece.name === 'b_king' && 
                 !main.variables.pieces['b_king'].moved && 
                 !main.variables.pieces['b_rook1'].moved &&
                 target.id === '3_8' &&
                 $('#2_8').attr('chess') === 'null' && 
                 $('#3_8').attr('chess') === 'null' &&
                 $('#4_8').attr('chess') === 'null') {
            
            main.variables.pieces['b_king'].position = '3_8';
            main.variables.pieces['b_king'].moved = true;
            $('#5_8').html('').attr('chess', 'null');
            $('#3_8').html(main.variables.pieces['b_king'].img)
                    .attr('chess', 'b_king');
            
            main.variables.pieces['b_rook1'].position = '4_8';
            main.variables.pieces['b_rook1'].moved = true;
            $('#1_8').html('').attr('chess', 'null');
            $('#4_8').html(main.variables.pieces['b_rook1'].img)
                    .attr('chess', 'b_rook1');
            
            main.methods.endturn();
        }
        else {
            main.methods.move(target);
            main.methods.endturn();
        }
      } else {
        main.methods.move(target);
        main.methods.endturn();
      }
    }
    else if (main.variables.selectedpiece !='' && target.name != 'null' && 
             target.id != selectedpiece.id && 
             selectedpiece.name.slice(0,1) != target.name.slice(0,1)) {
      
      if (selectedpiece.id != target.id && main.variables.highlighted.indexOf(target.id) != (-1)) {
        main.methods.capture(target);
        main.methods.endturn();
      }
    }
    else if (main.variables.selectedpiece !='' && target.name != 'null' && 
             target.id != selectedpiece.id && 
             selectedpiece.name.slice(0,1) == target.name.slice(0,1)) {

      main.methods.togglehighlight(main.variables.highlighted);
      main.variables.highlighted = [];
      main.variables.selectedpiece = target.id;
      main.methods.moveoptions(target.name);
    }
  });

  $('body').contextmenu(function(e) {
    e.preventDefault();
  });
});