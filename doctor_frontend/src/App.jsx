import { useState } from 'react';
import axios from 'axios';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  IconButton,
  AppBar,
  Toolbar,
  useTheme,
  Autocomplete,
  ClickAwayListener,
} from '@mui/material';

function App() {
  const [tcId, setTcId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [patientFound, setPatientFound] = useState(false);
  const [medicine, setMedicine] = useState('');
  const [prescriptionSubmitted, setPrescriptionSubmitted] = useState(false);
  const [medicines, setMedicines] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState(null);

  const theme = useTheme();
  const paleColors = {
    background: '#f8f9fa',
    primary: '#4a90e2',
    secondary: '#f5f5f5',
    success: '#e8f5e9',
    header: '#ffffff',
  };

  const handleTcSubmit = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('https://mocki.io/v1/d88264cd-79f7-4bb7-a4f6-b3ac52bebd68');
      if (response.data.exists) {
        setTimeout(() => {
          setPatientFound(true);
          setIsLoading(false);
        }, 100);
      }
    } catch (error) {
      console.error('Error:', error);
      setIsLoading(false);
    }
  };

  const handleAddMedicine = () => {
    if (medicine.trim()) {
      setMedicines([...medicines, { name: medicine, count: 1 }]);
      setMedicine('');
    }
  };

  const handleDeleteMedicine = (index) => {
    const newMedicines = medicines.filter((_, i) => i !== index);
    setMedicines(newMedicines);
  };

  const handleCountChange = (index, increment) => {
    const newMedicines = [...medicines];
    const newCount = newMedicines[index].count + increment;
    if (newCount >= 1) {
      newMedicines[index] = { ...newMedicines[index], count: newCount };
      setMedicines(newMedicines);
    }
  };

  const handleSubmitPrescription = () => {
    setPrescriptionSubmitted(true);
  };

  const searchMedicines = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) {
      console.log('Search term too short:', searchTerm);
      setSearchResults([]);
      return;
    }

    try {
      setIsSearching(true);
      console.log('Searching for:', searchTerm);
      const response = await axios.get(
        `/api/find-similar/${encodeURIComponent(searchTerm)}?limit=10`
      );
      console.log('Search response:', response.data);
      setSearchResults(response.data.similar_medicines);
    } catch (error) {
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Error data:', error.response.data);
        console.error('Error status:', error.response.status);
        console.error('Error headers:', error.response.headers);
      } else if (error.request) {
        // The request was made but no response was received
        console.error('Error request:', error.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error message:', error.message);
      }
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (event, newValue) => {
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    // Set new timeout to prevent too many API calls
    const newTimeout = setTimeout(() => {
      searchMedicines(newValue);
    }, 300);

    setSearchTimeout(newTimeout);
  };

  return (
    <>
      <AppBar position="static" sx={{ backgroundColor: paleColors.header, boxShadow: 1 }}>
        <Toolbar>
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              flexGrow: 1, 
              color: paleColors.primary,
              fontWeight: 600
            }}
          >
            Doctor Prescription Portal
          </Typography>
          {patientFound && (
            <Typography 
              variant="subtitle1" 
              sx={{ color: 'text.secondary' }}
            >
              Dr. John Doe
            </Typography>
          )}
        </Toolbar>
      </AppBar>

      <Container 
        maxWidth="md" 
        sx={{ 
          mt: 4, 
          minHeight: '90vh',
          backgroundColor: paleColors.background,
          borderRadius: 2,
          p: 4,
          boxShadow: '0 0 15px rgba(0,0,0,0.05)'
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {!patientFound ? (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              gap: 2,
              alignItems: 'center',
              p: 4,
              backgroundColor: '#fff',
              borderRadius: 2,
              boxShadow: '0 0 10px rgba(0,0,0,0.03)'
            }}>
              <Typography variant="h5" sx={{ mb: 2, color: 'text.primary' }}>
                Patient Verification
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  label="TC ID"
                  variant="outlined"
                  value={tcId}
                  onChange={(e) => setTcId(e.target.value)}
                  disabled={isLoading}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': {
                        borderColor: paleColors.primary,
                      },
                    },
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleTcSubmit}
                  disabled={isLoading || !tcId}
                  sx={{
                    backgroundColor: paleColors.primary,
                    '&:hover': {
                      backgroundColor: '#357abd',
                    }
                  }}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Verify Patient'}
                </Button>
              </Box>
            </Box>
          ) : (
            <>
              <Paper sx={{ p: 3, backgroundColor: '#fff', borderRadius: 2 }}>
                <Typography variant="h5" sx={{ color: paleColors.primary }}>
                  Patient: Ahmet Ali
                </Typography>
              </Paper>
              
              <Box sx={{ 
                display: 'flex', 
                gap: 2, 
                alignItems: 'center',
                backgroundColor: '#fff',
                p: 3,
                borderRadius: 2
              }}>
                <Autocomplete
                  freeSolo
                  options={searchResults}
                  value={medicine}
                  inputValue={medicine}
                  onInputChange={(event, newInputValue) => {
                    console.log('Input changed to:', newInputValue);
                    console.log('Current search results:', searchResults);
                    setMedicine(newInputValue);
                    handleSearchChange(event, newInputValue);
                  }}
                  onChange={(event, newValue) => {
                    console.log('Selection changed to:', newValue);
                    setMedicine(newValue || '');
                  }}
                  loading={isSearching}
                  sx={{ flexGrow: 1 }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Medicine Name"
                      variant="outlined"
                      size="small"
                      InputProps={{
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {isSearching ? <CircularProgress color="inherit" size={20} /> : null}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      }}
                    />
                  )}
                  renderOption={(props, option) => (
                    <Box 
                      component="li" 
                      {...props}
                      sx={{
                        p: 1,
                        '&:hover': {
                          backgroundColor: paleColors.background,
                        }
                      }}
                    >
                      {option}
                    </Box>
                  )}
                  noOptionsText={isSearching ? "Searching..." : "No medicines found"}
                  filterOptions={(x) => x}
                  isOptionEqualToValue={(option, value) => option === value}
                />
                <Button
                  variant="contained"
                  onClick={handleAddMedicine}
                  disabled={!medicine.trim()}
                  sx={{
                    backgroundColor: paleColors.primary,
                    '&:hover': {
                      backgroundColor: '#357abd',
                    },
                    whiteSpace: 'nowrap'
                  }}
                >
                  + Add Medicine
                </Button>
              </Box>

              <TableContainer component={Paper} sx={{ 
                mt: 3,
                borderRadius: 2,
                overflow: 'hidden'
              }}>
                <Table>
                  <TableHead>
                    <TableRow sx={{ backgroundColor: paleColors.secondary }}>
                      <TableCell>Medicine Name</TableCell>
                      <TableCell align="center">Quantity</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {medicines.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                          <Typography color="text.secondary">
                            No medicines added yet
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      medicines.map((med, index) => (
                        <TableRow key={index}>
                          <TableCell>{med.name}</TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                              <IconButton
                                size="small"
                                onClick={() => handleCountChange(index, -1)}
                                disabled={med.count <= 1}
                              >
                                −
                              </IconButton>
                              <Typography sx={{ minWidth: '30px', textAlign: 'center' }}>
                                {med.count}
                              </Typography>
                              <IconButton
                                size="small"
                                onClick={() => handleCountChange(index, 1)}
                              >
                                +
                              </IconButton>
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              onClick={() => handleDeleteMedicine(index)}
                              color="error"
                              size="small"
                            >
                              ×
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {medicines.length > 0 && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSubmitPrescription}
                  sx={{ 
                    mt: 2,
                    backgroundColor: paleColors.primary,
                    '&:hover': {
                      backgroundColor: '#357abd',
                    }
                  }}
                >
                  Submit Prescription
                </Button>
              )}

              {prescriptionSubmitted && (
                <Paper sx={{ 
                  p: 3, 
                  mt: 2, 
                  bgcolor: paleColors.success,
                  borderRadius: 2
                }}>
                  <Typography variant="h6" color="success.main">
                    Prescription submitted successfully!
                  </Typography>
                  <Typography>
                    Prescription ID: XXX
                  </Typography>
                </Paper>
              )}
            </>
          )}
        </Box>
      </Container>
    </>
  );
}

export default App; 