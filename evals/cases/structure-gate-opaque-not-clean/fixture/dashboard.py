"""Serves the dashboard. The page itself is the string below."""

DASHBOARD_JS = """
function renderDashboard(state) {
  var rows = [];
  if (state.filter1) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k1' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 1));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 1));
      }
    }
  }
  if (state.filter2) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k2' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 2));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 2));
      }
    }
  }
  if (state.filter3) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k3' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 3));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 3));
      }
    }
  }
  if (state.filter4) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k4' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 4));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 4));
      }
    }
  }
  if (state.filter5) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k5' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 5));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 5));
      }
    }
  }
  if (state.filter6) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k6' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 6));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 6));
      }
    }
  }
  if (state.filter7) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k7' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 7));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 7));
      }
    }
  }
  if (state.filter8) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k8' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 8));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 8));
      }
    }
  }
  if (state.filter9) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k9' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 9));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 9));
      }
    }
  }
  if (state.filter10) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k10' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 10));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 10));
      }
    }
  }
  if (state.filter11) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k11' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 11));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 11));
      }
    }
  }
  if (state.filter12) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k12' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 12));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 12));
      }
    }
  }
  if (state.filter13) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k13' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 13));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 13));
      }
    }
  }
  if (state.filter14) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k14' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 14));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 14));
      }
    }
  }
  if (state.filter15) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k15' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 15));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 15));
      }
    }
  }
  if (state.filter16) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k16' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 16));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 16));
      }
    }
  }
  if (state.filter17) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k17' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 17));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 17));
      }
    }
  }
  if (state.filter18) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k18' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 18));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 18));
      }
    }
  }
  if (state.filter19) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k19' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 19));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 19));
      }
    }
  }
  if (state.filter20) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k20' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 20));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 20));
      }
    }
  }
  if (state.filter21) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k21' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 21));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 21));
      }
    }
  }
  if (state.filter22) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k22' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 22));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 22));
      }
    }
  }
  if (state.filter23) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k23' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 23));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 23));
      }
    }
  }
  if (state.filter24) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k24' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 24));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 24));
      }
    }
  }
  if (state.filter25) {
    for (var j = 0; j < state.items.length; j++) {
      if (state.items[j].kind === 'k25' && state.items[j].active) {
        rows.push(formatRow(state.items[j], 25));
      } else if (state.items[j].fallback) {
        rows.push(formatRow(state.items[j].fallback, 25));
      }
    }
  }
  return rows.join('');
}
"""


def dashboard():
    return DASHBOARD_JS
