import { useState } from 'react';
import { MantineProvider, Container, TextInput, Button, Title, Paper, Table, Text, Alert, createTheme, MantineThemeOverride, Group, Loader } from '@mantine/core';
import axios from 'axios';
import './App.css';

// Configure axios with default config
const api = axios.create({
  baseURL: '', // Empty base URL since we're using relative paths with proxy
  headers: {
    'Content-Type': 'application/json',
  },
});

interface Medication {
  medicine_name: string;
  quantity: number;
}

interface PrescriptionResponse {
  status: string;
  prescription_group_id: number;
  medications: Medication[];
}

const theme: MantineThemeOverride = createTheme({
  primaryColor: 'blue',
  colors: {
    blue: [
      '#eef3ff',
      '#dce4ff',
      '#bac8ff',
      '#91a7ff',
      '#748ffc',
      '#5c7cfa',
      '#4c6ef5',
      '#4263eb',
      '#3b5bdb',
      '#364fc7',
    ],
  },
  fontFamily: "'Inter', -apple-system, system-ui, sans-serif",
  components: {
    Button: {
      styles: {
        root: {
          fontWeight: 600,
          letterSpacing: '0.01em',
          fontSize: '0.95rem',
        },
      },
    },
    TextInput: {
      styles: {
        input: {
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: '#748ffc',
          },
        },
      },
    },
  },
});

function App() {
  const [prescriptionId, setPrescriptionId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [prescriptionData, setPrescriptionData] = useState<PrescriptionResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setPrescriptionData(null);

    try {
      const response = await api.get(`/prescription/${prescriptionId}`);
      setPrescriptionData(response.data);
    } catch (err) {
      setError('Prescription not found. Please check the ID and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MantineProvider theme={theme}>
      <Container size="sm" className="pharmacy-container" style={{ marginTop: '3rem', marginBottom: '3rem' }}>
        <Paper shadow="sm" p={35} radius="lg" className="main-container">
          <Group align="center" justify="center" mb={40}>
            <Title order={1} className="main-title">
              Güneş Pharmacy
            </Title>
          </Group>

          <form onSubmit={handleSubmit}>
            <TextInput
              required
              label="Prescription ID"
              placeholder="Enter prescription ID"
              value={prescriptionId}
              onChange={(e) => setPrescriptionId(e.target.value)}
              size="md"
              radius="md"
              className="prescription-input"
              styles={{
                label: { 
                  marginBottom: 10,
                  color: '#1a1b1e',
                  fontSize: '1rem',
                  fontWeight: 600
                },
                input: {
                  '&:focus': { 
                    borderColor: '#4c6ef5',
                    boxShadow: '0 0 0 3px rgba(76, 110, 245, 0.1)'
                  },
                  height: '45px',
                  fontSize: '1rem',
                  border: '1.5px solid #e9ecef',
                  backgroundColor: '#ffffff',
                },
              }}
            />
            <Button
              type="submit"
              fullWidth
              loading={loading}
              size="md"
              mt="xl"
              radius="md"
              className="submit-button"
              style={{
                backgroundColor: '#4c6ef5',
                height: '45px',
                transition: 'all 0.2s ease',
              }}
              styles={{
                root: {
                  '&:hover': {
                    backgroundColor: '#4263eb',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(76, 110, 245, 0.2)',
                  },
                },
              }}
            >
              {loading ? <Loader size="sm" color="white" /> : 'Look up Prescription'}
            </Button>
          </form>

          {error && (
            <Alert
              color="red"
              radius="md"
              mt={30}
              className="error-alert"
              icon="⚠️"
            >
              {error}
            </Alert>
          )}

          {prescriptionData && (
            <div style={{ marginTop: '2.5rem' }} className="prescription-card">
              <Paper shadow="sm" p={30} radius="lg" className="info-card">
                <Text fw={700} size="xl" className="section-title">
                  Patient Information
                </Text>
                <Group gap={50}>
                  <div className="info-group">
                    <Text size="sm" c="dimmed" mb={8} className="field-label">Full Name</Text>
                    <Text fw={600} size="lg" className="field-value">Ahmet Ali</Text>
                  </div>
                  <div className="info-group">
                    <Text size="sm" c="dimmed" mb={8} className="field-label">TC ID</Text>
                    <Text fw={600} size="lg" className="field-value">12345678901</Text>
                  </div>
                  <div className="info-group">
                    <Text size="sm" c="dimmed" mb={8} className="field-label">Prescription ID</Text>
                    <Text fw={600} size="lg" className="field-value">{prescriptionData.prescription_group_id}</Text>
                  </div>
                </Group>
              </Paper>

              <div className="table-container">
                <Table
                  striped
                  highlightOnHover
                  withTableBorder
                  withColumnBorders
                  className="medications-table"
                >
                  <thead>
                    <tr>
                      <th>Medicine Name</th>
                      <th>Quantity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prescriptionData.medications.map((med, index) => (
                      <tr key={index} className="table-row">
                        <td>{med.medicine_name}</td>
                        <td>{med.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </div>
          )}
        </Paper>
      </Container>
    </MantineProvider>
  );
}

export default App;
